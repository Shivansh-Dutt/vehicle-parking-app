from datetime import datetime
from flask import render_template, request, redirect, session, url_for,flash
from models.models import db, ParkingLot, ParkingSpot, User,Reservation
from sqlalchemy import or_, func

def init_user_routes(app):

    # view profile and edit profile
    @app.route("/user/profile",methods=['post','get'])
    def user_profile():
        if 'user_id' not in session or session.get('user_role') != 'user':
            flash("login required", "warning")
            return redirect("/login")
        user_id = session.get("user_id")
        user = User.query.get(user_id) 
        if(request.method == "POST"):
            user.name = request.form['name']
            db.session.commit()
            flash("Edit successfull", "success")
            return redirect('/user/dashboard')
        return render_template("user/user_profile.html",user=user)

    # Release spot
    @app.route("/release/<int:r_id>", methods=['GET', 'POST'])
    def release_reservation(r_id):
        if 'user_id' not in session or session.get('user_role') != 'user':
            flash("Login required", "warning")
            return redirect("/login")

        reservation = Reservation.query.get(r_id)

        if not reservation:
            flash("No reservation with this ID", "danger")
            return redirect("/user/dashboard")

        if reservation.user_id != session.get("user_id"):
            flash("Unauthorized access to this reservation", "danger")
            return redirect("/user/dashboard")

        # Don't allow double release
        if reservation.leaving_timestamp:
            flash("This reservation has already been released.", "info")
            return redirect("/user/dashboard")

        # Calculate values only once
        leaving_time = datetime.now()
        duration = (leaving_time - reservation.parking_timestamp).total_seconds() / 3600
        duration = max(duration, 0.5)  # Enforce minimum billing
        parking_cost = round(reservation.spot.lot.price_per_hour * duration, 2)

        if request.method == "POST":
            # Update existing reservation
            reservation.leaving_timestamp = leaving_time
            reservation.parking_cost = parking_cost

            # Mark the spot as available
            reservation.spot.status = 'A'

            db.session.commit()

            flash(f"Spot released successfully! Total cost: ₹{parking_cost}", "success")
            return redirect("/user/dashboard")

        # Render confirmation page
        return render_template(
            "user/release_spot.html",
            reservation=reservation,
            leaving_time=leaving_time,
            parking_cost=parking_cost
        )

# Search Parking lot by address or pincode

    @app.route("/user/search", methods=["POST"])
    def search_parking():
        # Ensure the user is logged in and has the correct role
        if 'user_id' not in session or session.get('user_role') != 'user':
            flash("Login required", "warning")
            return redirect("/login")

        user_id = session.get('user_id')
        user = User.query.get_or_404(user_id)

        # Get reservation history
        reservations = Reservation.query.filter_by(user_id=user_id).order_by(
            Reservation.parking_timestamp.desc()
        ).all()

        # Get search input
        location = request.form.get('search_location', '').strip()

        if not location:
            flash("Please enter a location or pincode", "warning")
            return redirect("/user/dashboard")

        # Match by either pincode or address 
        lots = ParkingLot.query.filter(
            or_(
                ParkingLot.pincode == location,
                func.lower(ParkingLot.address).like(f"%{location.lower()}%")
            )
        ).all()

        if not lots:
            flash(f"No parking lots found for '{location}'.", "info")

        # available spots per lot
        available_spots_dict = {
            lot.id: ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            for lot in lots
        }

        return render_template(
            "user/user_dashboard.html",
            user=user,
            lots=lots,
            reservations=reservations,
            search_location=location,
            available_spots=available_spots_dict
        )

# book spot
    @app.route("/book/<int:lot_id>", methods=['GET', 'POST'])
    def book_spot(lot_id):
        if 'user_id' not in session or session.get('user_role') != 'user':
            flash("Login required", "warning")
            return redirect("/login")

        user_id = session.get("user_id")
        user = User.query.get(user_id)

        spot = ParkingSpot.query.filter(
            ParkingSpot.lot_id == lot_id,
            ParkingSpot.status == 'A'
        ).first()

        if request.method == "POST":
            if not spot:
                flash("No available spot", "danger")
                return redirect("/user/dashboard")

            vehicle_no = request.form["vehicle_number"]
            parking_time = datetime.now()  # ⬅️ Automatically set current time

            # Create booking
            reservation = Reservation(
                user_id=user.id,
                spot_id=spot.id,
                vehicle_no=vehicle_no,
                parking_timestamp=parking_time
            )

            # Mark spot as booked
            spot.status = 'O'

            db.session.add(reservation)
            db.session.commit()

            flash("Spot successfully booked!", "success")
            return redirect("/user/dashboard")

        return render_template("user/book_spot.html", spot=spot, user=user)

# View reservation history

    @app.route("/user/summary")
    def user_reservations():
        if session.get("user_role") != "user":
            return redirect("/login")
        
        user = User.query.get(session.get('user_id'))
        reservations = Reservation.query.filter(Reservation.user_id==user.id).order_by(Reservation.parking_timestamp.desc()).all()
        return render_template("user/summary.html", reservations=reservations,user=user)
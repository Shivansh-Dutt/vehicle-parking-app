from flask import render_template, request, redirect, session, url_for,flash
from models.models import db, ParkingLot, ParkingSpot, User ,Reservation
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

def init_admin_routes(app):
    
    # Create Parking Lot (with spots)
    @app.route("/admin/parking_lot/create", methods=["GET", "POST"])
    def create_parking_lot():
        #Only admin can access this page
        if session.get("user_role") != "admin":
            return redirect("/login")

        if request.method == "POST":
            # Get form data
            name = request.form.get("prime_location_name", "").strip()
            price = request.form.get("price_per_hour", "").strip()
            address = request.form.get("address", "").strip()
            pincode = request.form.get("pincode", "").strip()
            max_spots = request.form.get("max_spots", "").strip()

            # Validate presence of all fields
            if not all([name, price, address, pincode, max_spots]):
                flash("Fill all required fields", "warning")
                return redirect("/admin/parking_lot/create")

            # Validate and convert data types
            try:
                price = float(price)
                max_spots = int(max_spots)
                if price < 0 or max_spots <= 0:
                    raise ValueError
            except ValueError:
                flash("Enter valid positive numbers for price and max spots.", "warning")
                return redirect("/admin/parking_lot/create")

            if not pincode.isdigit() or len(pincode) != 6:
                flash("Enter a valid 6-digit pincode.", "warning")
                return redirect("/admin/parking_lot/create")

            # Create new ParkingLot
            try:
                new_lot = ParkingLot(
                    prime_location_name=name,
                    price_per_hour=price,
                    address=address,
                    pincode=pincode,
                    max_spots=max_spots
                )
                db.session.add(new_lot)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Database error while creating parking lot: {str(e)}", "danger")
                return redirect("/admin/parking_lot/create")

            # Create parking spots
            try:
                for i in range(1, max_spots + 1):
                    spot_number = f"{name[:3].upper()}-{i}"  # Unique spot number
                    spot = ParkingSpot(
                        spot_number=spot_number,
                        lot_id=new_lot.id,
                        status='A'  # Available by default
                    )
                    db.session.add(spot)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Database error while creating parking spots: {str(e)}", "danger")
                return redirect("/admin/parking_lot/create")

            flash("Parking lot created successfully!", "success")
            return redirect("/admin")

        # GET method: render the form
        return render_template("admin/create_parking_lot.html")


    # Edit Parking Lot

    @app.route("/admin/parking_lot/edit/<int:lot_id>", methods=["GET", "POST"])
    def edit_parking_lot(lot_id):
        if session.get("user_role") != "admin":
            return redirect("/login")

        lot = ParkingLot.query.get_or_404(lot_id)
        old_max_spots = lot.max_spots

        if request.method == "POST":
            try:
                name = request.form.get("prime_location_name", "").strip()
                price = request.form.get("price_per_hour", "").strip()
                address = request.form.get("address", "").strip()
                pincode = request.form.get("pincode", "").strip()
                new_max_spots_str = request.form.get("max_spots", "").strip()

                if not all([name, price, address, pincode, new_max_spots_str]):
                    flash("Please fill in all fields.", "warning")
                    return redirect(f"/admin/parking_lot/edit/{lot_id}")

                if not pincode.isdigit() or len(pincode) != 6:
                    flash("Enter a valid 6-digit pincode.", "warning")
                    return redirect(f"/admin/parking_lot/edit/{lot_id}")

                if not new_max_spots_str.isdigit():
                    flash("Max spots must be a valid number.", "warning")
                    return redirect(f"/admin/parking_lot/edit/{lot_id}")

                new_max_spots = int(new_max_spots_str)

                if new_max_spots > old_max_spots:
                    existing_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
                    for i in range(existing_spots + 1, new_max_spots + 1):
                        spot = ParkingSpot(
                            spot_number=f"S{i}",
                            status="A",
                            lot_id=lot.id
                        )
                        db.session.add(spot)

                elif new_max_spots < old_max_spots:
                    excess = old_max_spots - new_max_spots
                    deletable_spots = (
                        ParkingSpot.query
                        .filter_by(lot_id=lot.id, status="A")
                        .outerjoin(Reservation, Reservation.spot_id == ParkingSpot.id)
                        .filter(Reservation.id == None)
                        .order_by(ParkingSpot.id.desc())
                        .limit(excess)
                        .all()
                    )
                    if len(deletable_spots) < excess:
                        flash(f"Cannot reduce to {new_max_spots}. Only {len(deletable_spots)} empty spots available.", "warning")
                        return redirect(f"/admin/parking_lot/edit/{lot_id}")
                    for spot in deletable_spots:
                        db.session.delete(spot)

                # Update lot details
                lot.prime_location_name = name
                lot.price_per_hour = float(price)
                lot.address = address
                lot.pincode = pincode
                lot.max_spots = new_max_spots

                db.session.commit()
                flash("Parking lot updated successfully.", "success")
                return redirect("/admin")

            except ValueError:
                flash("Price must be a valid number.", "warning")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")

        return render_template("admin/edit_parking_lot.html", lot=lot)


    # Delete Parking Lot
    
    @app.route("/admin/lot/delete/<int:lot_id>", methods=["POST"])
    def delete_parking_lot(lot_id):
        lot = ParkingLot.query.get_or_404(lot_id)

        # Check for active reservations in any spot of this lot
        active_reservations = (
            db.session.query(Reservation)
            .join(ParkingSpot)
            .filter(ParkingSpot.lot_id == lot_id)
            .first()
        )

        if active_reservations:
            flash("Cannot delete lot. Some spots have or had reservations.", "danger")
            return redirect(url_for("admin_dashboard"))

        # Safe to delete
        db.session.delete(lot)
        db.session.commit()
        flash("Lot deleted successfully.", "success")
        return redirect(url_for("admin_dashboard"))


    # View Parking Lot Details & Spots

    @app.route("/admin/parking_lot/<int:lot_id>")
    def view_parking_lot(lot_id):
        if session.get("user_role") != "admin":
            return redirect("/login")

        lot = ParkingLot.query.get_or_404(lot_id)

        # Get the current page number from query string (default = 1)
        page = request.args.get("page", 1, type=int)

        # Paginate spots (10 per page)
        spots_pagination = ParkingSpot.query.filter_by(lot_id=lot_id).paginate(page=page, per_page=10)

        return render_template(
            "admin/view_parking_lot.html",
            lot=lot,
            spots=spots_pagination.items,
            pagination=spots_pagination
        )

    
    # view spot details
    
    @app.route("/admin/spot/<int:spot_id>")
    def view_spot(spot_id):
        if session.get("user_role") != "admin":
            return redirect("/login")

        spot = ParkingSpot.query.get_or_404(spot_id)
        reservation = Reservation.query.filter(Reservation.spot_id == spot_id,Reservation.leaving_timestamp==None).first()

        if not reservation:
            # No reservation found for this spot
            return render_template("admin/view_spot.html", spot=spot)

        # Calculate parking duration and cost
        leaving_time = datetime.now()
        duration = (leaving_time - reservation.parking_timestamp).total_seconds() / 3600
        duration = max(duration, 0.5)  # Minimum billing duration: 0.5 hours

        price_per_hour = reservation.spot.lot.price_per_hour
        parking_cost = round(price_per_hour * duration, 2)

        return render_template(
            "admin/view_spot_detail.html",
            spot=spot,
            reservation=reservation,
            parking_cost=parking_cost
        )
   
    # View All Users and their Reservations
    
    @app.route("/admin/users")
    def view_users():
        if session.get("user_role") != "admin":
            return redirect("/login")

        users = User.query.all()
        return render_template("admin/view_users.html", users=users)
    
    
     # Render admin search form
    @app.route("/admin/search")
    def search():
        if session.get("user_role") != "admin":
            return redirect("/login")
        return render_template("admin/search.html")

    # Handle parking lot search
    @app.route("/admin/search_lots", methods=["GET"])
    def search_parking_lots():
        if session.get("user_role") != "admin":
            return redirect("/login")

        search_by = request.args.get("search_by", "").lower()
        query = request.args.get("query", "").strip()

        if not search_by or not query:
            return render_template("admin/search_results.html", lots=[], error="Missing search parameters", search_by=search_by, query=query)

        filters = {
            "location": ParkingLot.prime_location_name,
            "address": ParkingLot.address,
            "pincode": ParkingLot.pincode,
            "price": ParkingLot.price_per_hour
        }

        attr = filters.get(search_by)
        if not attr:
            return render_template("admin/search_results.html", lots=[], error="Invalid search filter", search_by=search_by, query=query)

        try:
            if search_by == "price":
                price = float(query)
                lots = ParkingLot.query.filter(attr <= price).all()
            else:
                lots = ParkingLot.query.filter(attr.ilike(f"%{query}%")).all()
        except ValueError:
            return render_template("admin/search_results.html", lots=[], error="Invalid value for price", search_by=search_by, query=query)

        return render_template("admin/search_results.html", lots=lots, search_by=search_by, query=query)
    
    # Summary
    @app.route("/admin/reservations")
    def view_all_reservations():
        if session.get("user_role") != "admin":
            return redirect("/login")
        
        reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
        return render_template("admin/all_reservations.html", reservations=reservations)

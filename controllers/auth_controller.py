from flask import render_template, request, redirect, session, flash
from models.models import db, User,ParkingLot,Reservation,ParkingSpot
from werkzeug.security import generate_password_hash, check_password_hash

def init_auth_routes(app):

# route for root url
    @app.route('/')
    def home():
        if ('user_id') not in session:
            return redirect('/login')
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        return redirect("/admin" if user.role == "admin" else "/user/dashboard")

# registration
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email").strip()
            password = request.form.get("password").strip()
            name = request.form.get("name").strip()
            address = request.form.get("address").strip()
            pincode = request.form.get("pincode").strip()

            # admin email not allowed to register
            if email == "admin@parking.com":
                flash("Admin registration is not allowed.", "danger")
                return redirect("/register")

            # check all required field are there
            if not all([email, password, name]):
                flash("Fill all required fields", "warning")
                return redirect("/register")
            
            # check email already present
            if User.query.filter_by(email=email).first():
                flash("Email already registered", "danger")
                return redirect("/register")

            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
                address=address,
                pincode=pincode,
                role="user"
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect("/login")

        return render_template("register.html")

# login

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            
            # check is user exists
            if not user:
                flash("user does not exist", "danger")
                return redirect("/login")

            # check password
            if not check_password_hash(user.password, password):
                flash("Incorrect password", "danger")
                return redirect("/login")

            # stores login information in session 
            session['user_id'] = user.id
            session['user_role'] = user.role
            flash("Login successful!", "success")
            return redirect("/admin" if user.role == "admin" else "/user/dashboard")

        return render_template("login.html")

# user dashboard
    @app.route("/user/dashboard")
    def user_dashboard():
        # Ensure the user is logged in and has the correct role
        if 'user_id' not in session or session.get('user_role') != 'user':
            flash("Login required", "warning")
            return redirect("/login")

        user_id = session.get("user_id")
        user = User.query.get(user_id)
        lots = ParkingLot.query.all()

        # Dictionary to track available spots per lot
        available_spots_dict = {}
        for lot in lots:
            count = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            available_spots_dict[lot.id] = count

        # Get user's reservation history
        reservations = Reservation.query.filter_by(user_id=user_id).order_by(
            Reservation.parking_timestamp.desc()
        ).all()

        return render_template(
            "user/user_dashboard.html",
            user=user,
            reservations=reservations,
            lots=lots,
            available_spots=available_spots_dict
        )

# admin dashboard
    @app.route("/admin")
    def admin_dashboard():
        # check if logged in and is admin
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash("Admin login required.", "warning")
            return redirect("/login")
        parking_lots = ParkingLot.query.all()
                # Dictionary to track available spots per lot
        available_spots_dict = {}
        for lot in parking_lots:
            count = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            available_spots_dict[lot.id] = count
        return render_template("admin/admin_dashboard.html", lots=parking_lots,available_spots=available_spots_dict)
    
# logout
    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out successfully.", "info")
        return redirect("/login")

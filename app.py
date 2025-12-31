from flask import Flask
from werkzeug.security import generate_password_hash
from models.models import db, User
from config import Config
from controllers.auth_controller import init_auth_routes 
from controllers.admin_controller import init_admin_routes
from controllers.user_controller import init_user_routes

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def create_admin_user():
    with app.app_context():
        db.create_all()  # Create tables if not already created

        # Check if admin exists
        admin_email = "admin@parking.com"
        existing_admin = User.query.filter_by(email=admin_email).first()

        if not existing_admin:
            admin = User(
                name="Admin",
                email=admin_email,
                password=generate_password_hash("admin123"),  # hashed password
                role="admin",
                address="Admin HQ",
                pincode="000000"
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")

# Initialize the DB and create admin BEFORE first request
# @app.before_request
# def setup_app():
#     create_admin_user()
    
init_auth_routes(app)
init_admin_routes(app)
init_user_routes(app)

if __name__ == "__main__":
    app.run(debug=True)

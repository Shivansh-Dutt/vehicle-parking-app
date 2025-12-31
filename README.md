#  Vehicle Parking App

A role-based Flask web application that allows users to reserve parking spots and enables admin to manage parking lots and view reservation activity.

---

## 📌 Features

### 👤 User
- Register and login  
- Edit Profile
- View available parking lots   
- Reserve a parking spot by choosing lot and vehicle number  and first available spot in that lot will be reserved 
- Release the parking spot
- Search Spot by address and pincode
- View reservation history, duration, and cost 

### 👨‍💼 Admin
- Auto-created admin user (`admin@parking.com`, password: `admin123`)  
- Create, edit, and delete parking lots  
- Automatically generate parking spots based on max capacity  
- View all parking lots and their spot status (available/occupied)  
- Search Parking lot by location,address,pincode,price
- View all users and their reservations 

---

## 🗂 Project Structure

```
vehicle-parking-app/
│
├── app.py                  # Main Flask app
├── config.py               # App configuration (secret key, DB URI)
├── requirements.txt        # Dependencies
│
├── models/
│   └── models.py           # Datasbase Schema (User, ParkingLot, ParkingSpot, Reservation)
│
├── controllers/
│   ├── auth_controller.py  # Signup/Login logic 
│   ├── admin_controller.py # Admin-only routes 
│   └── user_controller.py  # Reservation and user routes
│
|── templates/               # Jinja2 HTML templates
│   ├── admin                # template folder for the admin     
|   |                         interface
│   ├── user                 # template folder for the user interface
│   ├── login.html,register.html  #templates for login and   registration
|   |
|   └──base.html   #base html file have flash and bootstrap setup 

```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/24f2002771/vehicle-parking-app.git
cd vehicle-parking-app
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
On Windows: venv\Scripts\activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

> On the first run:
> - Tables are created in `parking.sqlite3`  
> - Admin user is inserted (`admin@parking.com`, password: `admin123`)


### 5. Open in Browser

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔐 Default Admin Credentials

| Email              | Password   |
|-------------------|------------|
| admin@parking.com | admin123   |

> Only this admin is allowed; no manual admin registration is permitted.

---

## 🧪 Tech Stack

- **Backend**: Python, Flask  
- **Database**: SQLite with SQLAlchemy ORM  
- **Frontend**: HTML, Bootstrap (via Jinja2 templates)  
- **Routing Pattern**: `init_routes(app)` for each controller
- **Security**: Password hashing (`werkzeug.security`)  
- **Role-Based Access**: Controlled via session and user role  



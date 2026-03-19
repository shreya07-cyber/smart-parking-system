# 🅿️ Smart Parking Management System

A Python-based Smart Parking Management System that streamlines vehicle entry, exit, payment, and admin monitoring using QR codes, Flask web apps, and a Tkinter admin dashboard — all backed by a MySQL database.

---

## 📁 Project Structure

```
python_project/
├── Entry/
│   ├── app.py                      # Flask app for vehicle registration & slot allocation
│   ├── requirements.txt
│   ├── static/
│   │   ├── entry_qr.png            # QR code linking to the entry registration page
│   │   └── qr_<user_id>.png        # Per-user QR codes generated on registration
│   └── templates/
│       ├── register_vehicle.html   # Vehicle registration form
│       └── registration_success.html
├── Exit/
│   ├── app.py                      # Flask app for vehicle exit & payment processing
│   ├── requirements.txt
│   ├── static/
│   │   └── exit_qr.png             # QR code linking to the exit page
│   └── templates/
│       ├── exit_vehicle.html       # Exit form (enter User ID)
│       ├── payment.html            # Payment summary page
│       └── complete.html           # Exit confirmation page
└── admin.py                        # Tkinter admin dashboard with login
```

---

## ⚙️ Tech Stack

| Component        | Technology                          |
|-----------------|--------------------------------------|
| Entry/Exit UI    | Python Flask + HTML/Bootstrap        |
| Admin Dashboard  | Python Tkinter                       |
| Database         | MySQL (`mysql-connector-python`)     |
| QR Code          | `qrcode` + `Pillow (PIL)`            |
| Analytics Charts | `matplotlib`                         |
| Data Export      | Python `csv` module                  |

---

## 🗄️ Database Schema

### `parking_users`
| Column               | Type                        | Description                        |
|---------------------|-----------------------------|------------------------------------|
| `user_id`           | VARCHAR(20) PRIMARY KEY     | Auto-generated unique ID           |
| `name`              | VARCHAR(50)                 | User's name                        |
| `vehicle_no`        | VARCHAR(20)                 | Vehicle registration number        |
| `vehicle_type`      | VARCHAR(20)                 | `two_wheeler` or `four_wheeler`    |
| `preferred_exit_time` | TIME                      | User's expected exit time          |
| `slot_allocated`    | VARCHAR(10)                 | Assigned parking slot              |
| `entry_time`        | TIMESTAMP                   | Auto-set on registration           |
| `exit_time`         | TIMESTAMP (nullable)        | Set on exit                        |
| `total_charge`      | DECIMAL(10,2)               | Calculated parking fee             |
| `paid`              | VARCHAR(3)                  | `yes` or `no`                      |
| `status`            | ENUM(`parked`, `exited`)    | Current vehicle status             |

### `parking_slots`
| Column         | Type                         | Description                        |
|---------------|------------------------------|------------------------------------|
| `slot`        | VARCHAR(10) PRIMARY KEY      | Slot ID (e.g., `A1`, `D45`)        |
| `zone`        | VARCHAR(1)                   | Zone letter (A–E)                  |
| `vehicle_type`| VARCHAR(20)                  | `Two-Wheeler` or `Four-Wheeler`    |
| `status`      | ENUM(`free`, `occupied`)     | Current slot status                |

**Slot Layout:**
- Zones **A, B, C** → Two-Wheelers (50 slots each = **150 total**)
- Zones **D, E** → Four-Wheelers (100 slots each = **200 total**)

---

## 🔄 System Workflow

### 📥 Entry Flow
```
User scans Entry QR → Registration form (name, vehicle no, type, exit time)
       ↓
Slot allocated based on vehicle type & zone availability
       ↓
User ID generated → Stored in MySQL → Personal QR code displayed
```

### 📤 Exit Flow
```
User scans Exit QR → Enters User ID
       ↓
System fetches entry time, preferred exit, slot
       ↓
Calculates parking charge + penalty (if exit time exceeded)
       ↓
Payment confirmed → Slot freed → Record updated in DB
```

### 💰 Charge Calculation Logic

| Vehicle Type    | Base Charge (1st hr) | Per Extra Hour | Penalty (per hr over preferred time) |
|----------------|----------------------|----------------|---------------------------------------|
| Two-Wheeler     | ₹10                  | ₹20            | ₹20                                   |
| Four-Wheeler    | ₹30                  | ₹30            | ₹30                                   |

---

## 🖥️ Admin Dashboard Features

Accessible via `admin.py` (Tkinter GUI, password protected).

**Default credentials:**
```
Username: admin
Password: admin123
```

| Feature            | Description                                              |
|-------------------|----------------------------------------------------------|
| 📊 Dashboard       | Live metrics: parked vehicles, exits, available slots, today's income |
| 🚗 Parked Vehicles | Filter & view all parked vehicles; force exit; mark as paid |
| 🅿 Slot Availability | Bar chart of available vs occupied slots by vehicle type |
| 📈 Analytics       | Daily count, peak hours, income trends (last 7 days)     |
| ⚙ Manual Control  | Free or block any slot manually                          |
| 🔍 Search          | Search by Vehicle No, User ID, or Slot Number            |
| 📤 Export Data     | Export records as CSV for a selected date range          |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MySQL Server running locally
- pip

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smart-parking-system.git
cd smart-parking-system
```

### 2. Set Up MySQL Database
```sql
CREATE DATABASE parking_system;
```
> The tables (`parking_users`, `parking_slots`) are auto-created when you run the Entry app for the first time.

### 3. Configure Database Credentials

Update the `DB_CONFIG` in `Entry/app.py` and `Exit/app.py`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'database': 'parking_system'
}
```
Same for `admin.py`:
```python
self.db = mysql.connector.connect(
    host="localhost",
    user="your_mysql_username",
    password="your_mysql_password",
    database="parking_system"
)
```

### 4. Install Dependencies

**Entry app:**
```bash
cd Entry
pip install -r requirements.txt
```

**Exit app:**
```bash
cd Exit
pip install -r requirements.txt
```

**Admin dashboard:**
```bash
pip install mysql-connector-python matplotlib pillow
```

### 5. Run the Applications

Open **three separate terminals**:

```bash
# Terminal 1 – Entry System (port 5000)
cd Entry
python app.py

# Terminal 2 – Exit System (port 5002)
cd Exit
python app.py

# Terminal 3 – Admin Dashboard
python admin.py
```

> On startup, both Flask apps will auto-generate and display their QR codes (`entry_qr.png` and `exit_qr.png`).

---

## 📸 QR Code Usage

| QR Code       | Links To                              | Purpose                        |
|--------------|---------------------------------------|--------------------------------|
| `entry_qr.png` | `http://localhost:5000/`            | Scan to open registration form |
| `exit_qr.png`  | `http://localhost:5002/exit`        | Scan to start exit process     |
| `qr_<user_id>.png` | `http://localhost:5000/status/<user_id>` | Check individual parking status |

---

## 📌 Notes

- Both Flask servers must be running simultaneously for the full flow.
- Admin dashboard requires Tkinter (pre-installed with Python on most systems).
- The system simulates payment (no real payment gateway is integrated).
- For production use, change admin credentials and store them securely (e.g., hashed in DB).

---

## 📄 License

This project is built for educational purposes.

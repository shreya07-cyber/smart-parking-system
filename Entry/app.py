from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import qrcode
from PIL import Image
import random
import string
import os

app = Flask(__name__)

# Ensure directories exist
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'parking_system'
}

def show_entry_qr():
    """Generate and display QR code for entry"""
    entry_url = "http://192.168.51.215:5000/"  # URL for the entry page
    qr = qrcode.make(entry_url)
    qr_path = "static/entry_qr.png"
    qr.save(qr_path)
    img = Image.open(qr_path)
    img.show()
    print("Entry QR code generated and displayed")

def init_db():
    """Initialize database with required tables and slots"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create parking_users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking_users (
                user_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                vehicle_no VARCHAR(20) NOT NULL,
                vehicle_type VARCHAR(20) NOT NULL,
                preferred_exit_time TIME NOT NULL,
                slot_allocated VARCHAR(10),
                entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_time TIMESTAMP NULL,
                status ENUM('parked', 'exited') DEFAULT 'parked',
                UNIQUE(vehicle_no, status)
            )
        ''')
        
        # Create parking_slots table with zone information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking_slots (
                slot VARCHAR(10) PRIMARY KEY,
                zone VARCHAR(1) NOT NULL,
                vehicle_type VARCHAR(20) NOT NULL,
                status ENUM('free', 'occupied') DEFAULT 'free'
            )
        ''')
        
        # Initialize parking slots if they don't exist
        cursor.execute("SELECT COUNT(*) FROM parking_slots")
        if cursor.fetchone()[0] == 0:
            # Add two-wheeler slots in zones A, B, C (50 slots each zone)
            for zone in ['A', 'B', 'C']:
                for i in range(1, 51):
                    cursor.execute(
                        "INSERT INTO parking_slots (slot, zone, vehicle_type) VALUES (%s, %s, %s)",
                        (f"{zone}{i}", zone, "Two-Wheeler")
                    )
            
            # Add four-wheeler slots in zones D, E (100 slots each zone)
            for zone in ['D', 'E']:
                for i in range(1, 101):
                    cursor.execute(
                        "INSERT INTO parking_slots (slot, zone, vehicle_type) VALUES (%s, %s, %s)",
                        (f"{zone}{i}", zone, "Four-Wheeler")
                    )
            connection.commit()
            print("Parking slots initialized successfully!")
        
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def generate_user_id(name, vehicle_no):
    """Generate a unique user ID"""
    name_part = name[:2].upper() if len(name) >= 2 else 'XX'
    vehicle_part = vehicle_no[-4:].replace(' ', '').upper()
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{name_part}{vehicle_part}{random_part}"

def find_free_slot(vehicle_type):
    """Find and reserve a free slot for the vehicle type with zone preference"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Start transaction
        connection.start_transaction()
        
        # Map form input to database values
        vehicle_type_map = {
            'two_wheeler': 'Two-Wheeler',
            'four_wheeler': 'Four-Wheeler'
        }
        db_vehicle_type = vehicle_type_map.get(vehicle_type, vehicle_type)
        
        # Determine which zones to check based on vehicle type
        if db_vehicle_type == 'Two-Wheeler':
            zones = ['A', 'B', 'C']
        else:
            zones = ['D', 'E']
        
        # Try to find a free slot in preferred zones
        for zone in zones:
            cursor.execute('''
                SELECT slot FROM parking_slots 
                WHERE vehicle_type = %s AND zone = %s AND status = 'free' 
                LIMIT 1 FOR UPDATE
            ''', (db_vehicle_type, zone))
            
            slot = cursor.fetchone()
            if slot:
                slot_id = slot[0]
                # Mark slot as occupied
                cursor.execute('''
                    UPDATE parking_slots SET status = 'occupied' 
                    WHERE slot = %s
                ''', (slot_id,))
                connection.commit()
                return slot_id
        
        return None
        
    except Error as e:
        connection.rollback()
        print(f"Error finding free slot: {e}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def generate_user_qr(user_id):
    """Generate QR code for user status check"""
    status_url = f"http://localhost:5000/status/{user_id}"
    qr = qrcode.make(status_url)
    qr_path = f"static/qr_{user_id}.png"
    qr.save(qr_path)
    return qr_path

@app.route('/')
def home():
    """Entry point with QR code display"""
    return render_template('register_vehicle.html')

@app.route('/register', methods=['POST'])
def register():
    """Handle vehicle registration"""
    name = request.form['name']
    vehicle_no = request.form['vehicle_no'].strip().upper()
    vehicle_type = request.form['vehicle_type']
    preferred_exit_time = request.form['preferred_exit_time']
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if vehicle is already parked
        cursor.execute('''
            SELECT COUNT(*) FROM parking_users 
            WHERE vehicle_no = %s AND status = 'parked'
        ''', (vehicle_no,))
        if cursor.fetchone()[0] > 0:
            return "This vehicle is already parked!", 400
        
        # Find and allocate a slot
        slot_allocated = find_free_slot(vehicle_type)
        if not slot_allocated:
            return "No available slots for your vehicle type. Please try again later.", 400
        
        # Generate user ID
        user_id = generate_user_id(name, vehicle_no)
        
        # Insert user data
        cursor.execute('''
            INSERT INTO parking_users 
            (user_id, name, vehicle_no, vehicle_type, preferred_exit_time, slot_allocated)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, name, vehicle_no, vehicle_type, preferred_exit_time, slot_allocated))
        
        connection.commit()
        
        # Generate QR code
        qr_path = generate_user_qr(user_id)
        
        return render_template('registration_success.html', 
                             user_id=user_id,
                             name=name,
                             vehicle_no=vehicle_no,
                             slot_allocated=slot_allocated,
                             qr_path=qr_path)

    except Error as e:
        return f"Database Error: {e}", 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/status/<user_id>')
def status(user_id):
    """Show status of a specific parking user"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM parking_users 
            WHERE user_id = %s
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        
        if user_data:
            return render_template('user_status.html', user=user_data)
        else:
            return "User not found", 404
            
    except Error as e:
        return f"Database Error: {e}", 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    init_db()
    show_entry_qr()
    app.run(debug=True, host='0.0.0.0')
"""
doctor_auth.py - Doctor Authentication Service
"""
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
from config import DB_PATH, JWT_SECRET, TOKEN_EXPIRY_HOURS

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            specialization TEXT,
            phone TEXT,
            clinic_name TEXT,
            clinic_address TEXT,
            working_hours_start TEXT DEFAULT '09:00',
            working_hours_end TEXT DEFAULT '17:00',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Doctor sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            session_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Doctor database initialized")

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = "santeconnect-doctor"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def generate_token(doctor_id: int, email: str) -> str:
    """Generate simple token"""
    expiry = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    token_data = f"{doctor_id}:{email}:{expiry.timestamp()}"
    signature = hashlib.sha256(f"{token_data}{JWT_SECRET}".encode()).hexdigest()[:16]
    return f"doc_{doctor_id}:{signature}"

def verify_token(token: str) -> Optional[Dict]:
    """Verify token and return doctor info"""
    try:
        if not token.startswith("doc_"):
            return None
        
        parts = token[4:].split(":")
        if len(parts) != 2:
            return None
        
        doctor_id = int(parts[0])
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, name, specialization, phone, clinic_name, clinic_address,
                   working_hours_start, working_hours_end
            FROM doctors WHERE id = ? AND is_active = 1
        """, (doctor_id,))
        doctor = cursor.fetchone()
        conn.close()
        
        if doctor:
            return {
                "id": doctor["id"],
                "email": doctor["email"],
                "name": doctor["name"],
                "specialization": doctor["specialization"],
                "phone": doctor["phone"],
                "clinic_name": doctor["clinic_name"],
                "clinic_address": doctor["clinic_address"],
                "working_hours_start": doctor["working_hours_start"],
                "working_hours_end": doctor["working_hours_end"],
                "role": "doctor"
            }
        return None
    except:
        return None

def register_doctor(email: str, password: str, name: str, specialization: str = None, phone: str = None) -> Dict:
    """Register a new doctor"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM doctors WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Email already registered"}
    
    password_hash = hash_password(password)
    cursor.execute("""
        INSERT INTO doctors (email, password_hash, name, specialization, phone)
        VALUES (?, ?, ?, ?, ?)
    """, (email, password_hash, name, specialization, phone))
    conn.commit()
    doctor_id = cursor.lastrowid
    conn.close()
    
    token = generate_token(doctor_id, email)
    
    return {
        "success": True,
        "user": {
            "id": doctor_id,
            "email": email,
            "name": name,
            "specialization": specialization,
            "role": "doctor"
        },
        "token": token
    }

def login_doctor(email: str, password: str) -> Dict:
    """Login doctor"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute("""
        SELECT id, email, name, specialization, phone, clinic_name
        FROM doctors WHERE email = ? AND password_hash = ? AND is_active = 1
    """, (email, password_hash))
    doctor = cursor.fetchone()
    conn.close()
    
    if not doctor:
        return {"success": False, "error": "Invalid email or password"}
    
    token = generate_token(doctor["id"], doctor["email"])
    
    return {
        "success": True,
        "user": {
            "id": doctor["id"],
            "email": doctor["email"],
            "name": doctor["name"],
            "specialization": doctor["specialization"],
            "role": "doctor"
        },
        "token": token
    }

def update_doctor_profile(doctor_id: int, **kwargs) -> Dict:
    """Update doctor profile"""
    conn = get_db()
    cursor = conn.cursor()
    
    allowed_fields = ['name', 'specialization', 'phone', 'clinic_name', 'clinic_address',
                      'working_hours_start', 'working_hours_end']
    
    updates = []
    values = []
    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            updates.append(f"{field} = ?")
            values.append(value)
    
    if not updates:
        conn.close()
        return {"success": False, "error": "No valid fields to update"}
    
    values.append(doctor_id)
    cursor.execute(f"UPDATE doctors SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    
    return {"success": True}

# Initialize database on import
init_db()

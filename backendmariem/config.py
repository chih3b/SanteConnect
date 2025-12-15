"""
config.py - Configuration for Doctor Assistant Backend
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("DOCTOR_ASSISTANT_PORT", "8003"))

# Database
DB_PATH = os.getenv("DOCTOR_DB_PATH", "doctors.db")

# Google OAuth (for Calendar & Gmail)
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
CALENDAR_TOKEN_FILE = os.getenv("CALENDAR_TOKEN_FILE", "calendar_token.json")

# Upload settings
UPLOAD_DIR = "uploads"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# JWT Settings
JWT_SECRET = os.getenv("JWT_SECRET", "santeconnect-doctor-secret-key")
TOKEN_EXPIRY_HOURS = 24 * 7  # 7 days

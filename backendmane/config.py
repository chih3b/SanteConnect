"""
Medical Document Analysis Configuration
Backend - Port 8004
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8004

# LLaVA / TokenFactory Configuration
LLAVA_API_KEY = os.getenv("LLAVA_API_KEY", "")
LLAVA_BASE_URL = os.getenv("LLAVA_BASE_URL")

# SambaNova Configuration
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY", "")
SAMBANOVA_BASE_URL = os.getenv("SAMBANOVA_BASE_URL")

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
DOCTOR_PHONE = os.getenv("DOCTOR_PHONE", "")

# Upload Directory
UPLOAD_DIR = "uploads"

# CORS Origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "*"
]

"""
Mané (Medivise) Configuration
Medical Document Analysis Backend - Port 8004
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8004

# LLaVA / TokenFactory Configuration
LLAVA_API_KEY = os.getenv("LLAVA_API_KEY", "sk-47637ce473a547aea68df832427c298b")
LLAVA_BASE_URL = os.getenv("LLAVA_BASE_URL", "https://tokenfactory.esprit.tn/api")

# SambaNova Configuration
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY", "08bec77b-9055-442a-af63-0d3ab439a607")
SAMBANOVA_BASE_URL = os.getenv("SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1")

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACc468699f38a279ce08c85a483904afeb")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "4da9e532d95830cbdedbb4f9aa3e881e")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+14345058619")
DOCTOR_PHONE = os.getenv("DOCTOR_PHONE", "+21654708360")

# Upload Directory
UPLOAD_DIR = "uploads"

# CORS Origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "*"
]

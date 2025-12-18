"""
main.py - Doctor Assistant Backend API
Port 8003
"""
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
import uvicorn

from config import HOST, PORT, UPLOAD_DIR
from doctor_auth import (
    register_doctor, login_doctor, verify_token, update_doctor_profile, 
    change_doctor_password, init_db
)
from doctor_assistant import get_doctor_assistant
from mcp_tools import get_mcp_tools
from explainable_ai import get_xai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
Path(UPLOAD_DIR).mkdir(exist_ok=True)

app = FastAPI(
    title="SanteConnect Doctor Assistant API",
    description="AI-powered doctor assistant with appointments, email, and document processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ==================== MODELS ====================

class DoctorRegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    specialization: Optional[str] = None
    phone: Optional[str] = None

class DoctorLoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    phone: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


# ==================== AUTH DEPENDENCY ====================

def get_current_doctor(authorization: str = Header(None)):
    """Get current doctor from token"""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "")
    return verify_token(token)


# ==================== HEALTH ====================

@app.get("/")
async def root():
    return {
        "service": "SanteConnect Doctor Assistant API",
        "version": "1.0.0",
        "status": "running",
        "port": PORT
    }

@app.get("/api/health")
async def health():
    mcp = get_mcp_tools()
    return {
        "status": "healthy",
        "services": mcp.get_status(),
        "timestamp": datetime.now().isoformat()
    }


# ==================== DOCTOR AUTH ====================

@app.post("/auth/doctor/register")
async def register(request: DoctorRegisterRequest):
    """Register a new doctor"""
    result = register_doctor(
        email=request.email,
        password=request.password,
        name=request.name,
        specialization=request.specialization,
        phone=request.phone
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/doctor/login")
async def login(request: DoctorLoginRequest):
    """Login doctor"""
    result = login_doctor(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.get("/auth/doctor/me")
async def get_me(doctor: dict = Depends(get_current_doctor)):
    """Get current doctor info"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": doctor}

@app.put("/auth/doctor/profile")
async def update_profile(request: ProfileUpdateRequest, doctor: dict = Depends(get_current_doctor)):
    """Update doctor profile"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = update_doctor_profile(
        doctor["id"],
        name=request.name,
        specialization=request.specialization,
        phone=request.phone,
        clinic_name=request.clinic_name,
        clinic_address=request.clinic_address,
        working_hours_start=request.working_hours_start,
        working_hours_end=request.working_hours_end
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/doctor/profile/image")
async def upload_profile_image(file: UploadFile = File(...), doctor: dict = Depends(get_current_doctor)):
    """Upload doctor profile image"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    import uuid
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"doctor_{doctor['id']}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = Path(UPLOAD_DIR) / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    image_url = f"http://localhost:{PORT}/uploads/{filename}"
    result = update_doctor_profile(doctor["id"], profile_image=image_url)
    
    return result

@app.post("/auth/doctor/password")
async def change_password(request: PasswordChangeRequest, doctor: dict = Depends(get_current_doctor)):
    """Change doctor password"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = change_doctor_password(doctor["id"], request.old_password, request.new_password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ==================== AI ASSISTANT ====================

@app.post("/api/assistant/chat")
async def chat(request: ChatRequest, doctor: dict = Depends(get_current_doctor)):
    """Chat with AI assistant"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        assistant = get_doctor_assistant(doctor["id"], doctor["name"])
        result = await assistant.process_query(request.message)
        
        return {
            "response": result.get("response", ""),
            "session_id": assistant.session.session_id,
            "has_document": bool(assistant.session.current_document_content),
            "appointments_count": len(assistant.session.appointments),
            "xai_trace": result.get("xai_trace")
        }
    
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assistant/upload")
async def upload_document(file: UploadFile = File(...), doctor: dict = Depends(get_current_doctor)):
    """Upload and process a document"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        file_path = Path(UPLOAD_DIR) / f"{doctor['id']}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        assistant = get_doctor_assistant(doctor["id"], doctor["name"])
        result = await assistant.process_query(
            f"I uploaded a document: {file.filename}. Please extract and summarize it.",
            uploaded_file=str(file_path)
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "response": result.get("response", ""),
            "session_id": assistant.session.session_id,
            "xai_trace": result.get("xai_trace")
        }
    
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assistant/session")
async def get_session(doctor: dict = Depends(get_current_doctor)):
    """Get current session info"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        assistant = get_doctor_assistant(doctor["id"], doctor["name"])
        return {
            "session_id": assistant.session.session_id,
            "doctor_name": assistant.session.doctor_name,
            "message_count": len(assistant.session.conversation_history),
            "documents_count": len(assistant.session.uploaded_documents),
            "appointments_count": len(assistant.session.appointments),
            "current_document": assistant.session.current_document_name or None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assistant/status")
async def get_status(doctor: dict = Depends(get_current_doctor)):
    """Get assistant status"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        logger.info(f"🔍 Getting assistant for doctor: {doctor['id']}")
        assistant = get_doctor_assistant(doctor["id"], doctor["name"])
        mcp = get_mcp_tools()
        logger.info(f"✅ Assistant ready for doctor: {doctor['id']}")
        
        return {
            "assistant_ready": True,
            "session_id": assistant.session.session_id,
            "mcp_status": mcp.get_status()
        }
    except Exception as e:
        logger.error(f"❌ Assistant error: {e}")
        return {"assistant_ready": False, "error": str(e)}


# ==================== APPOINTMENTS ====================

@app.get("/api/appointments")
async def list_appointments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    doctor: dict = Depends(get_current_doctor)
):
    """List appointments from Google Calendar"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    mcp = get_mcp_tools()
    result = mcp.list_appointments(start_date, end_date)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error'))
    
    return {"appointments": result.get('appointments', []), "count": len(result.get('appointments', []))}

@app.get("/api/appointments/{appointment_id}")
async def get_appointment(appointment_id: str, doctor: dict = Depends(get_current_doctor)):
    """Get single appointment"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    mcp = get_mcp_tools()
    result = mcp.get_appointment(appointment_id)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return result.get('appointment')

@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, doctor: dict = Depends(get_current_doctor)):
    """Delete appointment"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    mcp = get_mcp_tools()
    result = mcp.delete_appointment(appointment_id)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))
    
    return {"message": "Appointment deleted", "id": appointment_id}


# ==================== XAI ====================

@app.get("/api/xai/metrics")
async def get_xai_metrics(doctor: dict = Depends(get_current_doctor)):
    """Get XAI metrics"""
    if not doctor:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    xai = get_xai()
    return {
        "success": True,
        "metrics": xai.get_metrics(),
        "recent_traces": xai.get_history(limit=10)
    }


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host=HOST, port=PORT)

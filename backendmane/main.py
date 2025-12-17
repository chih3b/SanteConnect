"""
Mané (Medivise) - Medical Document Analysis API
Port 8004
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import datetime
from pathlib import Path
import shutil
import logging

from config import API_HOST, API_PORT, UPLOAD_DIR, CORS_ORIGINS, DOCTOR_PHONE
from logic import analyser_patient, analyser_risque_et_recommandations, generer_synthese_medecin
from sms_notifier import sms_notifier
from ocr_tool import ocr_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mané (Medivise) API",
    description="Medical Document Analysis with OCR and AI Risk Assessment",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
Path(UPLOAD_DIR).mkdir(exist_ok=True)

# Global state for analyses history
ANALYSES_HISTORY: List[Dict] = []


# ==================== MODELS ====================

class AnalysisRequest(BaseModel):
    resume_texte: str

class DoctorPhoneRequest(BaseModel):
    phone: str


# ==================== UTILITY FUNCTIONS ====================

def extract_score(score_str: str) -> int:
    try:
        return int(str(score_str).rstrip('%').strip())
    except:
        return 0

def extract_patient_info(texte: str, analyse_complete: dict) -> dict:
    import re
    name_match = re.search(r'Name:\s*([^\n]+)', texte, re.IGNORECASE)
    patient_name = name_match.group(1).strip() if name_match else "Patient"
    
    age_match = re.search(r'Age:\s*(\d+)', texte, re.IGNORECASE)
    patient_age = age_match.group(1) if age_match else "N/A"
    
    score = extract_score(analyse_complete.get('score_rehospitalisation', '0%'))
    
    return {
        "name": patient_name[:30],
        "age": patient_age,
        "score": score,
        "diagnostic": analyse_complete.get('diagnostic_principal', 'À confirmer')[:50],
        "id": len(ANALYSES_HISTORY) + 1
    }

def save_to_history(texte: str, result: str, analyse_complete: dict, synthese_medecin: str):
    analysis_data = {
        'id': len(ANALYSES_HISTORY) + 1,
        'timestamp': datetime.datetime.now().isoformat(),
        'texte_preview': texte[:100] + "..." if len(texte) > 100 else texte,
        'diagnostic': analyse_complete.get('diagnostic_principal', 'Non spécifié'),
        'score': extract_score(analyse_complete.get('score_rehospitalisation', '0%')),
        'risks_count': len(analyse_complete.get('drapeaux_rouges', [])),
        'full_data': {
            'texte': texte,
            'result': result,
            'analyse_complete': analyse_complete,
            'synthese_medecin': synthese_medecin
        }
    }
    ANALYSES_HISTORY.append(analysis_data)
    if len(ANALYSES_HISTORY) > 50:
        ANALYSES_HISTORY.pop(0)

def count_analyses_last_days(days: int) -> int:
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    return len([a for a in ANALYSES_HISTORY if datetime.datetime.fromisoformat(a['timestamp']) > cutoff])

def calculate_avg_risks() -> float:
    if not ANALYSES_HISTORY:
        return 0
    return round(sum(a['risks_count'] for a in ANALYSES_HISTORY) / len(ANALYSES_HISTORY), 1)


# ==================== ROUTES ====================

@app.get("/")
async def root():
    return {
        "service": "Mané (Medivise) API",
        "version": "2.0.0",
        "status": "running",
        "port": API_PORT,
        "features": ["OCR", "AI Analysis", "Risk Assessment", "SMS Alerts"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "analyses_count": len(ANALYSES_HISTORY),
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.post("/api/analysis/image")
async def analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    resume_texte: Optional[str] = Form(None)
):
    """Analyze medical document from IMAGE with OCR + AI"""
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.pdf']:
            raise HTTPException(status_code=400, detail="Format non supporté. Utilisez JPG, PNG ou PDF")
        
        temp_path = Path(UPLOAD_DIR) / f"temp_{datetime.datetime.now().timestamp()}{file_ext}"
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Step 1: OCR - Extract text from image
        ocr_result = ocr_tool.process_document(str(temp_path))
        
        if not ocr_result.get('success'):
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"OCR failed: {ocr_result.get('error')}")
        
        extracted_text = ocr_result.get('text', '')
        
        # Combine with optional resume text
        full_text = f"{extracted_text}\n\n--- Résumé additionnel ---\n{resume_texte}" if resume_texte else extracted_text
        
        # Step 2: Coherence analysis with LLaVA
        result = analyser_patient(full_text, image_path=str(temp_path))
        
        # Step 3: Risk analysis and recommendations
        analyse_complete = analyser_risque_et_recommandations(result, full_text)
        
        # Step 4: Medical synthesis
        synthese_medecin = ""
        if isinstance(analyse_complete, dict) and "erreur" not in analyse_complete:
            synthese_medecin = generer_synthese_medecin(analyse_complete)
            save_to_history(full_text, result, analyse_complete, synthese_medecin)
            
            # SMS notification for high risk
            patient_info = extract_patient_info(full_text, analyse_complete)
            if patient_info["score"] > 10:
                doctor_phone = DOCTOR_PHONE
                background_tasks.add_task(sms_notifier.send_diagnostic_sms, doctor_phone, patient_info)
        
        temp_path.unlink(missing_ok=True)
        
        return {
            "id": len(ANALYSES_HISTORY),
            "timestamp": datetime.datetime.now().isoformat(),
            "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "ocr_method": ocr_result.get('method'),
            "result": result,
            "analyse_complete": analyse_complete,
            "synthese_medecin": synthese_medecin
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis")
async def analyze_text(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze from text only"""
    try:
        texte = request.resume_texte
        
        result = analyser_patient(texte, image_path=None)
        analyse_complete = analyser_risque_et_recommandations(result, texte)
        
        synthese_medecin = ""
        if isinstance(analyse_complete, dict) and "erreur" not in analyse_complete:
            synthese_medecin = generer_synthese_medecin(analyse_complete)
            save_to_history(texte, result, analyse_complete, synthese_medecin)
            
            patient_info = extract_patient_info(texte, analyse_complete)
            if patient_info["score"] > 10:
                background_tasks.add_task(sms_notifier.send_diagnostic_sms, DOCTOR_PHONE, patient_info)
        
        return {
            "id": len(ANALYSES_HISTORY),
            "timestamp": datetime.datetime.now().isoformat(),
            "result": result,
            "analyse_complete": analyse_complete,
            "synthese_medecin": synthese_medecin
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    if not ANALYSES_HISTORY:
        return {
            "total_analyses": 0, "average_score": 0, "high_risk_count": 0,
            "today_count": 0, "common_diagnosis": "Aucun", "trend": "N/A",
            "analyses_this_week": 0, "analyses_this_month": 0, "avg_risks_per_analysis": 0
        }
    
    from collections import Counter
    total = len(ANALYSES_HISTORY)
    scores = [a['score'] for a in ANALYSES_HISTORY if a['score'] > 0]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    high_risk = len([a for a in ANALYSES_HISTORY if a['score'] > 30])
    
    today = datetime.datetime.now().date()
    today_count = len([a for a in ANALYSES_HISTORY if datetime.datetime.fromisoformat(a['timestamp']).date() == today])
    
    diagnoses = [a['diagnostic'] for a in ANALYSES_HISTORY]
    most_common = Counter(diagnoses).most_common(1)
    common_diagnosis = f"{most_common[0][0]} ({most_common[0][1]}x)" if most_common else "Aucun"
    
    recent = [a['score'] for a in ANALYSES_HISTORY[-7:]]
    trend = "↗️ Hausse" if len(recent) >= 2 and recent[-1] > recent[-2] else "↘ Baisse" if len(recent) >= 2 and recent[-1] < recent[-2] else "N/A"
    
    return {
        "total_analyses": total, "average_score": avg_score, "high_risk_count": high_risk,
        "today_count": today_count, "common_diagnosis": common_diagnosis, "trend": trend,
        "analyses_this_week": count_analyses_last_days(7), "analyses_this_month": count_analyses_last_days(30),
        "avg_risks_per_analysis": calculate_avg_risks()
    }


@app.get("/api/dashboard/charts")
async def get_chart_data():
    """Get chart data for dashboard"""
    if not ANALYSES_HISTORY:
        return {'daily_counts': [], 'score_evolution': [], 'risk_distribution': [], 'diagnosis_distribution': []}
    
    from collections import Counter
    
    daily_counts = []
    for i in range(6, -1, -1):
        date = datetime.datetime.now().date() - datetime.timedelta(days=i)
        count = len([a for a in ANALYSES_HISTORY if datetime.datetime.fromisoformat(a['timestamp']).date() == date])
        daily_counts.append({'date': date.strftime('%a'), 'count': count})
    
    score_evolution = [{'index': i, 'score': a['score']} for i, a in enumerate(ANALYSES_HISTORY[-10:], 1)]
    
    risk_levels = {
        'Faible (0-15%)': len([a for a in ANALYSES_HISTORY if a['score'] <= 15]),
        'Modéré (16-30%)': len([a for a in ANALYSES_HISTORY if 15 < a['score'] <= 30]),
        'Élevé (31-50%)': len([a for a in ANALYSES_HISTORY if 30 < a['score'] <= 50]),
        'Critique (>50%)': len([a for a in ANALYSES_HISTORY if a['score'] > 50])
    }
    risk_distribution = [{'level': k, 'count': v} for k, v in risk_levels.items() if v > 0]
    
    diagnoses = [a['diagnostic'] for a in ANALYSES_HISTORY if a['diagnostic'] != 'Non spécifié']
    diagnosis_distribution = [{'diagnosis': k, 'count': v} for k, v in Counter(diagnoses).most_common(5)]
    
    return {
        'daily_counts': daily_counts,
        'score_evolution': score_evolution,
        'risk_distribution': risk_distribution,
        'diagnosis_distribution': diagnosis_distribution
    }


@app.get("/api/analyses")
async def get_recent_analyses(limit: int = 10):
    """Get recent analyses"""
    return {"analyses": ANALYSES_HISTORY[-limit:], "total": len(ANALYSES_HISTORY)}


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: int):
    """Get single analysis by ID"""
    for analysis in ANALYSES_HISTORY:
        if analysis['id'] == analysis_id:
            return analysis['full_data']
    raise HTTPException(status_code=404, detail="Analysis not found")


@app.post("/api/doctor-phone")
async def set_doctor_phone(request: DoctorPhoneRequest):
    """Set doctor phone number for SMS notifications"""
    if not request.phone.startswith('+'):
        raise HTTPException(status_code=400, detail="Format: +21612345678")
    return {'status': 'success', 'message': f'Numéro enregistré: {request.phone}'}


@app.post("/api/test-sms")
async def test_sms(request: DoctorPhoneRequest, background_tasks: BackgroundTasks):
    """Test SMS notification"""
    test_info = {'name': 'TEST Patient', 'age': '32', 'score': 25, 'diagnostic': 'Test', 'id': 999}
    background_tasks.add_task(sms_notifier.send_diagnostic_sms, request.phone, test_info)
    return {'status': 'success', 'message': 'SMS envoyé', 'phone': request.phone}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)

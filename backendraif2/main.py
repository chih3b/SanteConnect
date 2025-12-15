"""
Dr. Raif 2 - Assistant Médical IA
FastAPI Backend - Port 8002
"""

import sys
import traceback
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from config import config
from llm_client import llm_client
from embeddings import embeddings_client
from knowledge_loader import knowledge_loader
from vector_store import vector_store, rag_retriever
from symptom_detector import SymptomDetectorAgent
from disease_identifier import DiseaseIdentifierAgent
from conversation_agent import ConversationAgent
from report_generator import ReportGeneratorAgent
from email_agent import email_agent

# Sessions actives
active_sessions: Dict[str, Dict] = {}


def initialize_rag_system() -> bool:
    """Initialise le système RAG"""
    print("\n" + "=" * 60)
    print("🚀 INITIALISATION DU SYSTÈME RAG")
    print("=" * 60)
    
    try:
        print("\n📚 Chargement des connaissances médicales...")
        documents, metadata = knowledge_loader.load_all_knowledge()
        
        if not documents:
            print("⚠️ Aucun document chargé")
            return False
        
        print(f"   ✓ {len(documents)} documents chargés")
        
        print("\n🔧 Génération des embeddings...")
        embeddings = embeddings_client.embed_batch(documents, show_progress=True)
        print(f"   ✓ {len(embeddings)} embeddings générés")
        
        print("\n🔧 Indexation dans FAISS...")
        vector_store.clear()
        vector_store.add_documents(embeddings, documents, metadata)
        print(f"   ✓ {vector_store.total_documents} documents indexés")
        
        print("\n💾 Sauvegarde de l'index...")
        vector_store.save(str(config.FAISS_PERSIST_PATH))
        
        rag_retriever.set_embeddings_client(embeddings_client)
        
        print("\n" + "=" * 60)
        print("✅ SYSTÈME RAG INITIALISÉ")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur initialisation RAG: {e}")
        traceback.print_exc()
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de l'application"""
    print("\n" + "=" * 70)
    print("  🏥 DR. RAIF 2 - ASSISTANT MÉDICAL IA")
    print(f"  Port: {config.API_PORT}")
    print("=" * 70)
    
    if vector_store.total_documents == 0:
        loaded = vector_store.load(str(config.FAISS_PERSIST_PATH))
        if loaded and vector_store.total_documents > 0:
            print(f"✅ Index FAISS chargé: {vector_store.total_documents} documents")
            knowledge_loader.load_all_knowledge()
            rag_retriever.set_embeddings_client(embeddings_client)
        else:
            print("🔧 Création de l'index RAG...")
            initialize_rag_system()
    
    print(f"\n✅ Système démarré!")
    print(f"📍 API: http://localhost:{config.API_PORT}")
    print(f"📍 Docs: http://localhost:{config.API_PORT}/docs\n")
    
    yield
    
    print("\n⚠️ Arrêt du système...")
    vector_store.save(str(config.FAISS_PERSIST_PATH))
    llm_client.close()
    print("✅ Système arrêté\n")


app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Report generator
report_generator = ReportGeneratorAgent(llm_client)


# ==================== MODÈLES ====================

class SessionCreate(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=100)
    patient_email: Optional[str] = None
    doctor_email: Optional[str] = config.DEFAULT_DOCTOR_EMAIL

class ChatMessage(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=2000)

class EmailRequest(BaseModel):
    session_id: str
    doctor_email: str

class ChatResponse(BaseModel):
    response: str
    formatted_response: str
    detected_symptoms: List[str] = []
    new_symptoms: List[str] = []
    identified_disease: Optional[Dict] = None
    possible_diseases: List[Dict] = []
    urgency_level: str = ""
    phase: str = "initial"
    should_end: bool = False
    message_count: int = 0


# ==================== HELPERS ====================

def get_or_create_session(session_id: str, patient_name: str = "Patient", patient_email: str = None, doctor_email: str = None) -> Dict:
    """Récupère ou crée une session"""
    if session_id not in active_sessions:
        symptom_detector = SymptomDetectorAgent(llm_client, embeddings_client, rag_retriever)
        disease_identifier = DiseaseIdentifierAgent(llm_client, embeddings_client, rag_retriever, knowledge_loader)
        
        active_sessions[session_id] = {
            "id": session_id,
            "patient_name": patient_name,
            "patient_email": patient_email,
            "doctor_email": doctor_email or config.DEFAULT_DOCTOR_EMAIL,
            "created_at": datetime.now().isoformat(),
            "agent": ConversationAgent(
                llm_client=llm_client,
                symptom_detector=symptom_detector,
                disease_identifier=disease_identifier,
                embeddings_client=embeddings_client,
                rag_retriever=rag_retriever
            )
        }
        print(f"✅ Session créée: {session_id}")
    return active_sessions[session_id]


async def generate_and_send_report(session_id: str) -> bool:
    """Génère et envoie le rapport médical"""
    try:
        session = active_sessions.get(session_id)
        if not session:
            return False
        
        agent = session["agent"]
        conversation_data = agent.export_conversation()
        
        patient_info = {
            "name": session["patient_name"],
            "email": session.get("patient_email", ""),
            "session_id": session_id
        }
        
        print(f"📝 Génération du rapport pour {patient_info['name']}...")
        report = report_generator.generate_medical_report(conversation_data, patient_info, session_id)
        
        if config.AUTO_SEND_REPORT:
            doctor_email = session.get("doctor_email") or config.DEFAULT_DOCTOR_EMAIL
            diagnosis = conversation_data.get("diagnosis", {})
            urgency = diagnosis.get("primary_disease", {}).get("urgency", "Modéré") if diagnosis.get("primary_disease") else "Modéré"
            
            email_result = email_agent.send_medical_report(
                doctor_email=doctor_email,
                patient_name=patient_info["name"],
                report_html=report.get("report_html", ""),
                report_text=report.get("report_text", ""),
                session_id=session_id,
                urgency_level=urgency
            )
            
            if email_result.get("success"):
                print(f"✅ Rapport envoyé à {doctor_email}")
            else:
                print(f"⚠️ Échec envoi email: {email_result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        traceback.print_exc()
        return False


# ==================== ROUTES ====================

@app.get("/")
async def root():
    """Page d'accueil"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Dr. Raif 2 - Assistant Médical IA</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 20px; padding: 40px; }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .feature { background: rgba(255, 255, 255, 0.2); padding: 15px; margin: 10px 0; border-radius: 10px; }
        a { color: white; background: rgba(255, 255, 255, 0.2); padding: 10px 20px; border-radius: 5px; text-decoration: none; display: inline-block; margin: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Dr. Raif 2</h1>
        <p>Assistant Médical IA - Port 8002</p>
        <h2>✨ Fonctionnalités</h2>
        <div class="feature">🩺 Détection de symptômes avec RAG</div>
        <div class="feature">🔬 Identification de maladies</div>
        <div class="feature">💬 Conversation naturelle</div>
        <div class="feature">📄 Génération de rapports médicaux</div>
        <div class="feature">📧 Envoi automatique d'emails</div>
        <h2>📚 Documentation</h2>
        <a href="/docs">API Docs</a>
        <a href="/health">Health Check</a>
    </div>
</body>
</html>
    """)


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": config.API_VERSION,
        "port": config.API_PORT,
        "rag_documents": vector_store.total_documents,
        "active_sessions": len(active_sessions),
        "knowledge": knowledge_loader.get_statistics()
    }


@app.post("/api/session/create")
async def create_session(data: SessionCreate):
    """Crée une nouvelle session"""
    import uuid
    session_id = str(uuid.uuid4())
    session = get_or_create_session(session_id, data.patient_name, data.patient_email, data.doctor_email)
    
    return {
        "session_id": session_id,
        "patient_name": data.patient_name,
        "created_at": session["created_at"],
        "status": "active"
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Récupère une session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session = active_sessions[session_id]
    agent = session["agent"]
    
    return {
        "session_id": session_id,
        "patient_name": session["patient_name"],
        "created_at": session["created_at"],
        "message_count": agent.message_count,
        "phase": agent.conversation_phase,
        "detected_symptoms": agent.symptom_detector.detected_symptoms
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Endpoint de chat principal"""
    try:
        session = get_or_create_session(message.session_id)
        agent = session["agent"]
        
        print(f"\n📨 Message - Session: {message.session_id[:8]}...")
        print(f"   Message: {message.message[:100]}...")
        
        response = agent.process_message(patient_message=message.message, session_id=message.session_id)
        
        print(f"   ✅ Réponse générée (phase: {response['phase']})")
        
        # Générer et envoyer le rapport si consultation terminée
        if response.get("should_end") and response.get("identified_disease"):
            await generate_and_send_report(message.session_id)
        
        return ChatResponse(**response)
        
    except Exception as e:
        print(f"❌ Erreur chat: {e}")
        traceback.print_exc()
        
        return ChatResponse(
            response="Je suis désolé, une erreur s'est produite. Pouvez-vous reformuler?",
            formatted_response="Je suis désolé, une erreur s'est produite. Pouvez-vous reformuler?",
            detected_symptoms=[],
            new_symptoms=[],
            identified_disease=None,
            possible_diseases=[],
            urgency_level="",
            phase="initial",
            should_end=False,
            message_count=0
        )


@app.post("/api/report/send-email")
async def send_report_email(request: EmailRequest):
    """Envoie le rapport par email"""
    try:
        session = active_sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        agent = session["agent"]
        conversation_data = agent.export_conversation()
        
        patient_info = {
            "name": session["patient_name"],
            "email": session.get("patient_email", ""),
            "session_id": request.session_id
        }
        
        report = report_generator.generate_medical_report(conversation_data, patient_info, request.session_id)
        
        diagnosis = conversation_data.get("diagnosis", {})
        urgency = diagnosis.get("primary_disease", {}).get("urgency", "Modéré") if diagnosis.get("primary_disease") else "Modéré"
        
        result = email_agent.send_medical_report(
            doctor_email=request.doctor_email,
            patient_name=patient_info["name"],
            report_html=report.get("report_html", ""),
            report_text=report.get("report_text", ""),
            session_id=request.session_id,
            urgency_level=urgency
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur envoi email: {str(e)}")


@app.delete("/api/session/{session_id}")
async def close_session(session_id: str):
    """Ferme une session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"message": "Session fermée", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session non trouvée")


@app.get("/api/knowledge/diseases")
async def get_diseases():
    """Liste toutes les maladies"""
    diseases = knowledge_loader.get_all_diseases()
    return {"diseases": diseases, "total": len(diseases)}


@app.get("/api/knowledge/statistics")
async def get_statistics():
    """Statistiques de la base de connaissances"""
    return knowledge_loader.get_statistics()


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.API_HOST, port=config.API_PORT, reload=config.DEBUG)

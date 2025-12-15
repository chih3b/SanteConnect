"""
Dr. MediBot - FastAPI Backend
Medical consultation chatbot with RAG System
Runs on port 8001 to avoid conflict with SanteConnect main backend (8000)
"""

import sys
import io
import base64
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI, OpenAIError
from gtts import gTTS

from config import (
    API_KEY, API_BASE_URL, MODEL_NAME,
    MODEL_TEMPERATURE, MODEL_MAX_TOKENS, MODEL_TOP_P,
    SYSTEM_PROMPT, EMERGENCY_KEYWORDS,
    CONNECTION_TIMEOUT, READ_TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    API_PORT
)
from rag_system import initialize_rag_system, MedicalRAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('medibot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variables
rag_system: Optional[MedicalRAGSystem] = None
openai_client: Optional[OpenAI] = None
sessions: Dict[str, Dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global rag_system, openai_client
    
    logger.info("=" * 60)
    logger.info(f"Starting Dr. MediBot on port {API_PORT}")
    logger.info("=" * 60)
    
    # Initialize OpenAI client
    http_client = httpx.Client(
        verify=False,  # For ESPRIT API
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        ),
        timeout=httpx.Timeout(
            timeout=READ_TIMEOUT,
            connect=CONNECTION_TIMEOUT,
            read=READ_TIMEOUT,
            write=10.0,
            pool=5.0
        )
    )
    
    openai_client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
        http_client=http_client,
        max_retries=MAX_RETRIES,
        timeout=READ_TIMEOUT
    )
    logger.info(f"OpenAI client initialized (base_url={API_BASE_URL})")
    
    # Test API connection
    try:
        logger.info("Testing API connection...")
        test_response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        logger.info("✓ API connection successful")
    except Exception as e:
        logger.error(f"✗ API connection failed: {e}")
        logger.warning("Continuing anyway, but API calls may fail...")
    
    # Initialize RAG system
    rag_system = initialize_rag_system()
    logger.info(f"RAG system ready: {rag_system.index.ntotal} diseases indexed")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Dr. MediBot...")
    if http_client:
        http_client.close()


# Create FastAPI app
app = FastAPI(
    title="Dr. MediBot API",
    description="Medical consultation chatbot with RAG",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware - allow frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(default="default")


class ChatResponse(BaseModel):
    response: str
    audio_base64: Optional[str] = None
    potential_diseases: List[Dict[str, Any]] = []
    is_emergency: bool = False
    rag_similarity: float = 0
    session_messages: int = 0
    processing_time: Dict[str, float] = {}


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


# Helper functions
def get_session(session_id: str) -> Dict:
    """Get or create session"""
    if session_id not in sessions:
        sessions[session_id] = {
            'history': [],
            'created_at': datetime.now().isoformat(),
            'message_count': 0
        }
    return sessions[session_id]


def add_to_history(session_id: str, role: str, content: str):
    """Add message to session history"""
    session = get_session(session_id)
    session['history'].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })
    session['message_count'] = len(session['history'])


def text_to_speech(text: str, lang: str = 'fr') -> Optional[bytes]:
    """Convert text to speech"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp.read()
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None


def format_rag_context(search_results: List[Dict]) -> str:
    """Format RAG search results for LLM context"""
    if not search_results:
        return "Aucune maladie correspondante trouvée."
    
    context_parts = ["=== BASE DE CONNAISSANCES MÉDICALE ===\n"]
    
    for result in search_results:
        disease_name = result['name']
        similarity = result['similarity_score']
        symptoms = result['symptoms']
        questions_diag = result.get('questions_diagnostic', [])
        drapeaux = result.get('drapeaux_rouges', [])
        
        context_parts.append(f"\n--- MALADIE #{result['rank']}: {disease_name} ---")
        context_parts.append(f"Similarité: {similarity}%")
        
        if symptoms:
            context_parts.append(f"\nSymptômes principaux:")
            for sym in symptoms[:8]:
                context_parts.append(f"  • {sym}")
        
        if questions_diag:
            context_parts.append(f"\nQuestions à poser:")
            for q in questions_diag[:5]:
                context_parts.append(f"  ❓ {q}")
        
        if drapeaux:
            context_parts.append(f"\nDrapeaux rouges:")
            for d in drapeaux[:4]:
                context_parts.append(f"  ⚠️ {d}")
    
    return "\n".join(context_parts)


def check_emergency(text: str, search_results: List[Dict]) -> bool:
    """Check if message indicates emergency - only triggers on explicit emergency keywords"""
    text_lower = text.lower()
    
    # Only check for explicit emergency keywords in the text
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text_lower:
            return True
    
    # Don't trigger emergency based on RAG results alone - too many false positives
    # Only trigger if urgency score is very high (9+) AND similarity is high (80%+)
    if search_results:
        top_result = search_results[0]
        urgency = top_result.get('score_gravite', {}).get('urgence', 0)
        similarity = top_result.get('similarity_score', 0)
        if urgency >= 9 and similarity >= 80:
            return True
    
    return False


def call_llm_with_retry(messages: List[Dict], max_attempts: int = 3) -> str:
    """Call LLM with retry logic"""
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"LLM call attempt {attempt}/{max_attempts}")
            
            response = openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=MODEL_TEMPERATURE,
                max_tokens=MODEL_MAX_TOKENS,
                top_p=MODEL_TOP_P,
                timeout=READ_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except httpx.ConnectTimeout as e:
            last_error = f"Connection timeout: {e}"
            logger.warning(f"Attempt {attempt} failed: Connection timeout")
            
        except httpx.ReadTimeout as e:
            last_error = f"Read timeout: {e}"
            logger.warning(f"Attempt {attempt} failed: Read timeout")
            
        except httpx.ConnectError as e:
            last_error = f"Connection error: {e}"
            logger.warning(f"Attempt {attempt} failed: Connection error")
            
        except OpenAIError as e:
            last_error = f"OpenAI API error: {e}"
            logger.warning(f"Attempt {attempt} failed: {e}")
            
        except Exception as e:
            last_error = f"Unexpected error: {e}"
            logger.error(f"Attempt {attempt} failed with unexpected error: {e}")
        
        if attempt < max_attempts:
            time.sleep(RETRY_DELAY * attempt)
    
    raise Exception(f"LLM call failed after {max_attempts} attempts. Last error: {last_error}")


# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Dr. MediBot API", "status": "running", "port": API_PORT}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "rag_index_size": rag_system.index.ntotal if rag_system else 0,
        "model": MODEL_NAME,
        "api_base": API_BASE_URL
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with RAG"""
    global rag_system, openai_client
    
    user_message = request.message.strip()
    session_id = request.session_id
    
    logger.info(f"Chat message from {session_id}: {user_message[:100]}...")
    
    # Add to history
    add_to_history(session_id, 'user', user_message)
    
    # RAG Search
    search_start = time.time()
    search_results = rag_system.search(user_message, top_k=5)
    search_time = time.time() - search_start
    
    if search_results:
        logger.info(f"Top match: {search_results[0]['name']} ({search_results[0]['similarity_score']}%)")
    
    # Format context
    rag_context = format_rag_context(search_results)
    
    # Build messages for LLM
    session = get_session(session_id)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"CONTEXTE MEDICAL:\n{rag_context}"}
    ]
    
    # Add conversation history
    for msg in session['history'][-12:]:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })
    
    # Call LLM with retry
    try:
        llm_start = time.time()
        assistant_message = call_llm_with_retry(messages, max_attempts=MAX_RETRIES)
        llm_time = time.time() - llm_start
        
        logger.info(f"LLM response received in {llm_time:.3f}s")
        
        # Add to history
        add_to_history(session_id, 'assistant', assistant_message)
        
        # Generate TTS
        audio_base64 = None
        try:
            audio_bytes = text_to_speech(assistant_message)
            if audio_bytes:
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
        
        # Check emergency
        is_emergency = check_emergency(assistant_message, search_results)
        
        # Extract potential diseases
        potential_diseases = []
        for result in search_results[:3]:
            potential_diseases.append({
                'name': result['name'],
                'confidence': result['similarity_score'],
                'category': result['category'],
                'symptoms': result['symptoms'][:5]
            })
        
        return ChatResponse(
            response=assistant_message,
            audio_base64=audio_base64,
            potential_diseases=potential_diseases,
            is_emergency=is_emergency,
            rag_similarity=search_results[0]['similarity_score'] if search_results else 0,
            session_messages=session['message_count'],
            processing_time={
                'rag_search': round(search_time, 3),
                'llm_generation': round(llm_time, 3),
                'total': round(search_time + llm_time, 3)
            }
        )
        
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        
        fallback_message = (
            "Je rencontre actuellement des difficultés de connexion. "
            "Veuillez réessayer dans quelques instants. "
            "Si vous avez une urgence médicale, appelez le 190 (SAMU) ou le 197 (Pompiers)."
        )
        
        return ChatResponse(
            response=fallback_message,
            audio_base64=None,
            potential_diseases=[],
            is_emergency=False,
            rag_similarity=0,
            session_messages=session['message_count'],
            processing_time={'error': str(e)}
        )


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Text-to-speech synthesis"""
    try:
        audio_bytes = text_to_speech(request.text)
        if audio_bytes:
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return {"audio_base64": audio_base64}
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
    except Exception as e:
        logger.error(f"Synthesize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    session = get_session(session_id)
    return {
        "session_id": session_id,
        "message_count": session['message_count'],
        "created_at": session['created_at'],
        "history_length": len(session['history'])
    }


@app.post("/session/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear session history"""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "success", "message": "Session cleared"}


@app.post("/rebuild-index")
async def rebuild_index():
    """Rebuild FAISS index"""
    global rag_system
    
    try:
        rag_system.load_medical_data()
        count = rag_system.build_index()
        rag_system.save_index()
        
        return {
            "status": "success",
            "diseases_indexed": count
        }
    except Exception as e:
        logger.error(f"Index rebuild failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Fatigue Detection Models
class FatigueReport(BaseModel):
    eye_aspect_ratio: float = Field(default=1.0)
    is_yawning: bool = Field(default=False)
    blink_count: int = Field(default=0)
    fatigue_level: str = Field(default="none")
    timestamp: str = Field(default="")


# Store fatigue data per session
fatigue_data: Dict[str, List[Dict]] = {}


@app.post("/fatigue/report")
async def report_fatigue(report: FatigueReport):
    """Receive fatigue detection data from frontend"""
    try:
        # Store fatigue data (could be used for analytics)
        session_key = "default"
        if session_key not in fatigue_data:
            fatigue_data[session_key] = []
        
        fatigue_data[session_key].append({
            "ear": report.eye_aspect_ratio,
            "yawning": report.is_yawning,
            "blinks": report.blink_count,
            "level": report.fatigue_level,
            "timestamp": report.timestamp
        })
        
        # Keep only last 100 entries
        if len(fatigue_data[session_key]) > 100:
            fatigue_data[session_key] = fatigue_data[session_key][-100:]
        
        # Log high fatigue
        if report.fatigue_level == "high":
            logger.warning(f"High fatigue detected! EAR: {report.eye_aspect_ratio:.2f}")
        
        return {"status": "received", "level": report.fatigue_level}
    except Exception as e:
        logger.error(f"Fatigue report error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/fatigue/stats")
async def get_fatigue_stats():
    """Get fatigue statistics"""
    session_key = "default"
    if session_key not in fatigue_data or not fatigue_data[session_key]:
        return {"status": "no_data"}
    
    data = fatigue_data[session_key]
    avg_ear = sum(d["ear"] for d in data) / len(data)
    total_yawns = sum(1 for d in data if d["yawning"])
    high_fatigue_count = sum(1 for d in data if d["level"] == "high")
    
    return {
        "total_reports": len(data),
        "average_ear": round(avg_ear, 3),
        "yawn_events": total_yawns,
        "high_fatigue_events": high_fatigue_count,
        "latest_level": data[-1]["level"] if data else "none"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, reload=True)

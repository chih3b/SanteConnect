"""
Configuration pour Dr. Raif 2 - Assistant Médical IA
Port 8002 pour éviter les conflits avec SanteConnect (8000) et MediBot (8001)
"""

from pathlib import Path


class Config:
    # API Settings
    API_TITLE = "Dr. Raif 2 - Assistant Médical IA"
    API_DESCRIPTION = "Chatbot médical intelligent avec RAG et multi-agents"
    API_VERSION = "2.0.0"
    API_HOST = "0.0.0.0"
    API_PORT = 8002
    DEBUG = True
    
    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    
    # LLM API - ESPRIT Token Factory
    LLM_API_KEY = "sk-e16d16a054744585bfb2ef09bb52315c"
    LLM_API_BASE = "https://tokenfactory.esprit.tn/api"
    LLM_MODEL = "hosted_vllm/Llama-3.1-70B-Instruct"
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 2000
    LLM_TOP_P = 0.9
    
    # Timeouts
    CONNECTION_TIMEOUT = 30.0
    READ_TIMEOUT = 120.0
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0
    
    # Paths
    BASE_DIR = Path(__file__).parent
    MEDICAL_KNOWLEDGE_DIR = BASE_DIR / "medical_knowledge"
    FAISS_PERSIST_PATH = BASE_DIR / "faiss_index"
    DATABASE_PATH = BASE_DIR / "raif_sessions.db"
    
    # Email Configuration
    AUTO_SEND_REPORT = True
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "raifguizani10@gmail.com"
    SENDER_PASSWORD = "belqmggnhzokzjus"
    DEFAULT_DOCTOR_EMAIL = "raifguizani10@gmail.com"
    
    # Embeddings
    EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-m"
    EMBEDDING_DIMENSION = 768
    
    # RAG Configuration
    RAG_TOP_K = 5
    RAG_CONFIDENCE_THRESHOLD = 0.6
    
    # Symptom Detection
    SYMPTOM_CONFIDENCE_THRESHOLD = 0.6
    MIN_SYMPTOMS_FOR_DIAGNOSIS = 2
    
    # Report Configuration
    REPORT_LANGUAGE = "fr"
    REPORT_FORMAT = "html"


config = Config()

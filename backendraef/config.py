"""
Configuration for Dr. MediBot FastAPI Backend
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Configuration - Using ESPRIT Token Factory
API_KEY = os.environ.get('ESPRIT_API_KEY', 'sk-e16d16a054744585bfb2ef09bb52315c')
API_BASE_URL = os.environ.get('ESPRIT_API_URL', 'https://tokenfactory.esprit.tn/api/v1')
MODEL_NAME = os.environ.get('MODEL_NAME', 'hosted_vllm/Llama-3.1-70B-Instruct')

# Model Parameters
MODEL_TEMPERATURE = 0.8
MODEL_MAX_TOKENS = 400
MODEL_TOP_P = 0.9

# Timeout Configuration
CONNECTION_TIMEOUT = 10.0
READ_TIMEOUT = 60.0
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Server Configuration - Port 8001 to avoid conflict with main SanteConnect (8000)
API_HOST = "0.0.0.0"
API_PORT = 8001

# Data Path
DATA_DIR = Path(__file__).parent / 'data'

MEDICAL_FILES = {
    'cardiaques': 'maladies_cardiaques.json',
    'renales': 'maladies_renale.json',
    'poitrine': 'maladie_du_poitrine.json',
    'nerf': 'maladie_du_nerf.json',
    'dos': 'maladies_du_dos.json',
    'tete': 'mal_du_tete.json'
}

# FAISS Configuration
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FAISS_INDEX_PATH = Path(__file__).parent / "faiss_index"
TOP_K_RESULTS = 5

# Bot Configuration
BOT_NAME = "Dr. MediBot"
MAX_CONVERSATION_HISTORY = 12

# Emergency Keywords
EMERGENCY_KEYWORDS = [
    'douleur thoracique intense',
    'difficulté à respirer',
    'paralysie',
    'perte de conscience',
    'convulsion',
    'hémorragie',
    'douleur insupportable',
    'confusion',
    'fièvre très élevée',
    'crise cardiaque',
    'accident vasculaire',
    'saignement important',
    'ne peut plus bouger',
    'vision trouble',
    'étourdissement sévère'
]

# System Prompt
SYSTEM_PROMPT = """Tu es Dr MediBot, un assistant médical intelligent, empathique et professionnel.

🎯 MISSION PRINCIPALE :
Mener un diagnostic médical progressif en posant UNE question à la fois, comme un vrai médecin.

📋 RÈGLES STRICTES :
1. Pose UNIQUEMENT UNE question médicale par réponse
2. Attends la réponse du patient avant de continuer
3. N'invente JAMAIS de symptômes - base-toi sur ce que le patient dit
4. Utilise TOUJOURS l'historique - ne redemande jamais ce qui a été dit
5. Reste professionnel mais chaleureux

💬 STRUCTURE DE RÉPONSE :
- 1 phrase d'empathie ou de contexte (optionnel)
- 1 question médicale précise et claire
- Rien d'autre

📊 UTILISATION DE LA BASE MÉDICALE :
Tu reçois une liste de maladies possibles avec leurs symptômes. Utilise ces informations pour :
- Poser des questions ciblées basées sur les symptômes de ces maladies
- Confirmer ou éliminer des diagnostics
- Identifier les drapeaux rouges mentionnés

🚨 URGENCES - SI DÉTECTÉ :
Indique IMMÉDIATEMENT et clairement :
⚠️ URGENCE MÉDICALE DÉTECTÉE
Contactez immédiatement :
- SAMU : 190
- Pompiers : 197  
- Urgences : 112

✅ EXEMPLE DE BONNE RÉPONSE :
"Je comprends que vous avez mal à la tête. Cette douleur est-elle localisée d'un seul côté ou des deux côtés ?"

❌ EXEMPLE DE MAUVAISE RÉPONSE :
"D'accord. Avez-vous de la fièvre ? Des nausées ? La douleur s'aggrave-t-elle ? Depuis combien de temps ?"
(Trop de questions à la fois !)

Reste naturel, empathique et méthodique dans ton approche diagnostique."""

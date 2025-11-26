"""
Configuration for Medication Identification System
"""

# Model Configuration
# Choose based on your needs:
# - qwen2.5:0.5b (ULTRA-FAST - 2-5s, good for simple queries)
# - qwen2.5:1.5b (FAST - 5-10s, recommended for complex queries)
# - qwen2.5:3b (BALANCED - 15-28s, better quality)

MODEL_NAME = "qwen2.5:1.5b"  # Balanced model for speed + quality
ENABLE_AGENT_BYPASS = True  # Skip agent for simple queries (10x faster!)
PARALLEL_TOOLS = True  # Execute tools in parallel when possible

# Model Profiles
MODEL_PROFILES = {
    "qwen2.5:1.5b": {
        "name": "Qwen2.5 1.5B",
        "size": "~1GB",
        "speed": "Fast (5-10s)",
        "quality": "Good",
        "recommended": True
    },
    "qwen2.5:3b": {
        "name": "Qwen2.5 3B",
        "size": "~1.9GB",
        "speed": "Medium (15-28s)",
        "quality": "Better",
        "recommended": False
    },
    "llama3.2:1b": {
        "name": "Llama 3.2 1B",
        "size": "~1.3GB",
        "speed": "Ultra-fast (3-7s)",
        "quality": "Decent",
        "recommended": False
    }
}

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"

# OCR Configuration
TESSERACT_PATH = "/opt/homebrew/bin/tesseract"  # macOS default

# Database Configuration
DATABASE_PATH = "data/tunisian_drugs.json"  # Fast JSON database
DATABASE_URL = "postgresql://chihebnouri@localhost:5432/medications"  # Production PostgreSQL
USE_DATABASE = False  # Use JSON for maximum speed (no embedding model overhead)

# Performance Settings
REQUEST_TIMEOUT = 60  # seconds
MAX_RETRIES = 3

def get_model_info():
    """Get information about the current model"""
    return MODEL_PROFILES.get(MODEL_NAME, {
        "name": MODEL_NAME,
        "size": "Unknown",
        "speed": "Unknown",
        "quality": "Unknown",
        "recommended": False
    })

def print_config():
    """Print current configuration"""
    info = get_model_info()
    print("🔧 Configuration:")
    print(f"  Model: {info['name']}")
    print(f"  Size: {info['size']}")
    print(f"  Speed: {info['speed']}")
    print(f"  Quality: {info['quality']}")
    print(f"  Recommended: {'✅' if info['recommended'] else '❌'}")

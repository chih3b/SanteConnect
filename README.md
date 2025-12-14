# 🏥 SanteConnect - AI Medication Identification System

An intelligent medication identification and information system for Tunisia, powered by state-of-the-art AI and computer vision.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![React](https://img.shields.io/badge/react-18+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🎯 Core Functionality
- 📸 **Camera Capture**: Take photos directly from your webcam
- 🔍 **Image Recognition**: Upload or capture medication images for instant identification
- 💊 **Comprehensive Drug Info**: Detailed information about 30 Tunisian medications
- 🤖 **AI Chat Assistant**: Interactive chatbot with animated avatar for medication queries
- 🔎 **Smart Search**: Fuzzy search with OCR error correction
- ⚡ **Lightning Fast**: 0.5-3 second response times with intelligent caching

### 🧠 AI Capabilities
- **Multi-OCR System**: EasyOCR (primary) + LLaVA vision model (fallback)
- **Intelligent Routing**: Fast path for simple queries, AI agent for complex ones
- **Fuzzy Matching**: Handles OCR errors and typos (e.g., "Célestène" → "Celestene")
- **Active Ingredient Search**: Find medications by ingredient (e.g., "paracétamol" → Doliprane)
- **Drug Comparison**: Safe substitution analysis with medical warnings
- **Interaction Checking**: Identifies dangerous drug combinations

### 🎨 Modern UI/UX
- Clean, modern design with blue glow effects
- Animated chat interface with typing indicators
- Responsive layout for all devices
- Real-time loading states
- Professional card-based design

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **AI Agent**: LangGraph + Ollama (qwen2.5:1.5b)
- **OCR**: EasyOCR (primary), LLaVA (fallback)
- **Vision**: OpenCV, Pillow
- **Caching**: In-memory cache with 30min TTL

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS + shadcn/ui
- **Icons**: Lucide React
- **Build**: Create React App

### Database
- **Type**: JSON file (optimized for 30 medications)
- **Size**: ~50KB
- **Query Time**: <1ms

## 📦 Installation

### Prerequisites

```bash
# Required
- Python 3.8+
- Node.js 16+
- Ollama with models:
  - qwen2.5:1.5b (AI reasoning)
  - llava (vision fallback)
```

### 1. Clone Repository

```bash
git clone https://github.com/chih3b/SanteConnect.git
cd SanteConnect
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Ollama models
ollama pull qwen2.5:1.5b
ollama pull llava

# Start backend server
uvicorn main:app --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
```

The app will open at `http://localhost:3000`

## 🚀 Usage

### 1. Medication Identification
- Click "Identify" tab
- **Option A**: Drag & drop an image
- **Option B**: Click "Take Photo" to use your camera
- Click "Identify Medication"
- Get instant results with detailed information

### 2. Search Medications
- Click "Search" tab
- Type medication name (handles typos!)
- View results with similarity scores

### 3. AI Assistant
- Click "AI Assistant" tab
- Ask questions like:
  - "What is Doliprane used for?"
  - "Can I take Advil with Aspirine?"
  - "What medicine for fever?"
  - "Alternatives to Voltarène?"

## 📊 Database

**30 Tunisian Medications** including:

| Category | Medications |
|----------|-------------|
| **Pain/Fever** | Doliprane, Efferalgan, Paracétamol, Advil, Fervex |
| **Anti-inflammatory** | Voltarène, Inflamyl, Inflamyl Fort |
| **Antibiotics** | Amoxicilline, Augmentin, Flagyl, Zithromax |
| **Digestive** | Oméprazole, Mopral, Mesopral, Inexium, Spasfon |
| **Cardiovascular** | Aspirine, Kardégic |
| **Other** | Lexomil, Calmoss, Xanax, Celestene, Daflon, Ventoline, Seretide, Lyrica, Levothyrox |

## 🎯 Performance

| Query Type | Response Time | Accuracy |
|------------|---------------|----------|
| Clear Images | <1s | 100% |
| Blurry Images | 1-3s | 90%+ |
| Simple Queries | 0.01-0.1s | 100% |
| Complex Queries | 5-30s | 95%+ |
| Cache Hit | <0.01s | 100% |

## 🔧 Configuration

Edit `config.py` to customize:

```python
MODEL_NAME = "qwen2.5:1.5b"  # AI model
OLLAMA_BASE_URL = "http://localhost:11434"
USE_DATABASE = False  # Set True for vector DB
```

## 📝 API Endpoints

```
GET  /                      - Health check
POST /agent/identify        - Identify medication from image
GET  /agent/query          - Ask AI assistant
GET  /search/{query}       - Search medications
GET  /fast/{query}         - Fast path lookup
GET  /stats                - System statistics
POST /cache/clear          - Clear cache
```

## 🏗️ Architecture

```
┌─────────────────┐
│   React Frontend│
│  (Tailwind CSS) │
└────────┬────────┘
         │
    ┌────▼────┐
    │ FastAPI │
    └────┬────┘
         │
    ┌────┴─────┐
    │          │
┌───▼───┐  ┌──▼──────┐
│EasyOCR│  │LangGraph│
│       │  │  Agent  │
└───┬───┘  └──┬──────┘
    │         │
    └────┬────┘
         │
    ┌────▼────┐
    │  JSON   │
    │Database │
    └─────────┘
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Disclaimer

This system is for **informational purposes only**. Always consult a healthcare professional before making decisions about medications.

## 📄 License

MIT License - see LICENSE file for details

## 👨‍💻 Author

**Chiheb Nouri**
- GitHub: [@chih3b](https://github.com/chih3b)

## 🙏 Acknowledgments

- Ollama for local AI models
- EasyOCR for accurate text recognition
- LangGraph for agentic workflows
- shadcn/ui for beautiful components

---

Made with ❤️ for Tunisia 🇹🇳

---

# 📋 Advanced Prescription Scanner Module

## 🆕 New Features (v2.1)

The **Prescription Scanner** module adds powerful medical document processing capabilities:

### 📄 Prescription Scanning
- **SAM2 Image Segmentation**: Meta's Segment Anything 2 model for precise text region detection
- **Azure Vision OCR**: Microsoft's cloud OCR for accurate text extraction from prescriptions
- **Multi-Agent Architecture**: Specialized AI agents for each processing step

### 🔒 HIPAA Compliance
- **PHI Detection & Redaction**: Automatically detects and redacts Protected Health Information
- **Named Entity Recognition**: Uses BERT-based NER to identify names, addresses, IDs
- **Regex-based Fallback**: Pattern matching for SSN, phone numbers, dates, etc.

### 💊 Drug Intelligence
- **Vector Database Search**: FAISS-based semantic search across medication database
- **FDA API Integration**: Real-time drug information from FDA OpenFDA API
- **RxNorm API Integration**: NIH's normalized medication naming system
- **LLaMA AI Fallback**: AI-generated drug information when APIs unavailable

### 🌐 Cloud Integration
- **HuggingFace Hub**: Model and database storage (free tier)
- **Azure Cognitive Services**: Vision API for OCR
- **OpenRouter API**: Access to various LLM providers

---

## 🔑 Environment Setup

### Step 1: Create `.env` file in `backend/` folder

Create a file named `.env` inside the `backend/` directory:

```bash
cd backend
touch .env  # On Windows: type nul > .env
```

### Step 2: Add API Keys

Edit `backend/.env` with your API credentials:

```env
# ===========================================
# AZURE COGNITIVE SERVICES (Required for OCR)
# ===========================================
# Get from: https://portal.azure.com → Create "Computer Vision" resource
AZURE_VISION_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-azure-vision-api-key

# ===========================================
# HUGGINGFACE (Required for models & database)
# ===========================================
# Get from: https://huggingface.co/settings/tokens
HF_TOKEN=hf_your_huggingface_token

# SAM2 Model Repository (for image segmentation)
SAM2_HF_REPO=firasaa/sam2-medical-ocr

# Medication Vector Database Repository
HF_MEDICATION_DB_REPO=firasaa/medication-vector-db

# ===========================================
# OPENROUTER (Required for AI drug info)
# ===========================================
# Get from: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key
GROK_MODEL=anthropic/claude-3.5-sonnet

# ===========================================
# OPTIONAL: NER Model for PHI detection
# ===========================================
HF_NER_MODEL=dslim/bert-base-NER
```

### Step 3: Get Your API Keys

#### 🔷 Azure Vision API (for OCR)

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search **"Computer Vision"**
3. Create the resource (Free tier: 5,000 calls/month)
4. Go to **Keys and Endpoint** → Copy **KEY 1** and **Endpoint**

#### 🟠 HuggingFace Token (for models)

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Click **New token** → Give it a name
3. Select **Read** access (or Write if uploading)
4. Copy the token

#### 🟢 OpenRouter API (for AI)

1. Go to [OpenRouter](https://openrouter.ai/keys)
2. Sign up / Log in
3. Click **Create Key**
4. Copy the API key

---

## 🏗️ Backend Architecture

```
backend/
├── .env                        # API keys and configuration
├── agent_system.py             # Main agent orchestration system
├── medication_vector_db.py     # FAISS vector database with HF Hub sync
├── drugs.json                  # Local drug database (200+ medications)
├── agents/
│   ├── orchestrator.py         # Routes requests to appropriate agents
│   ├── ocr_agent.py            # Coordinates OCR processing
│   ├── segmentation_agent.py   # SAM2 image segmentation
│   ├── text_recognition_agent.py # Azure Vision OCR
│   ├── phi_filter_agent.py     # HIPAA PHI redaction
│   ├── drug_information_agent.py # Drug lookup & alternatives
│   └── tools.py                # Reusable tools for agents
├── segment-anything-2/         # SAM2 model package
└── checkpoints/                # Downloaded model weights
```

### Agent Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESCRIPTION SCAN FLOW                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. IMAGE INPUT                                              │
│     • Upload prescription photo (JPEG, PNG)                  │
│     • Base64 encoded for processing                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. SEGMENTATION AGENT (SAM2)                                │
│     • Detect text regions in image                           │
│     • Segment prescription into readable areas               │
│     • Fallback: Use full image if segmentation fails         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TEXT RECOGNITION AGENT (Azure Vision)                    │
│     • OCR on segmented regions                               │
│     • Extract text from prescription                         │
│     • Handle handwritten + printed text                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. PHI FILTER AGENT (HIPAA Compliance)                      │
│     • NER-based entity detection (names, locations)          │
│     • Regex patterns (SSN, phone, dates, IDs)                │
│     • Redact: "John Smith" → "[PERSON_REDACTED]"             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. MEDICATION EXTRACTION                                    │
│     • Regex patterns for drug names + dosages                │
│     • Match against known medication database                │
│     • Extract: "Doliprane 1000mg" → {name, dosage}           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. DRUG INFORMATION AGENT                                   │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│     │ Vector DB   │  │  FDA API    │  │ RxNorm API  │       │
│     │ (FAISS)     │  │             │  │             │       │
│     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│            │                │                │               │
│            └────────────────┴────────────────┘               │
│                             │                                │
│                             ▼                                │
│     ┌─────────────────────────────────────────────────┐     │
│     │  LLaMA AI Fallback (via OpenRouter)              │     │
│     │  If no results from APIs, use AI to generate     │     │
│     └─────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. RESPONSE                                                 │
│     • Extracted text (redacted if PHI filter enabled)        │
│     • Medications found with dosages                         │
│     • Drug alternatives with sources                         │
│     • AI-generated information                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Additional Installation Steps

### 1. Install SAM2 (Segment Anything 2)

```bash
cd backend/segment-anything-2
pip install -e .
```

### 2. Install Backend Dependencies

```bash
pip install sentence-transformers faiss-cpu huggingface-hub python-dotenv
```

### 3. Build & Upload Vector Database (Optional)

If you want to create your own medication database:

```bash
cd backend
python build_and_upload_db.py
```

This will:
- Load medications from `drugs.json`
- Create FAISS embeddings using SentenceTransformers
- Upload to HuggingFace Hub (requires write access token)

---

## 📝 New API Endpoints

```
POST /prescription/scan      - Scan prescription image
     Query params:
       - filter_phi: bool    - Enable HIPAA PHI redaction (default: true)
     Body: multipart/form-data with 'file' field
     
GET  /prescription/status    - Check if agent system is ready
```

### Example Response

```json
{
  "success": true,
  "extracted_text": "Dr. [PERSON_REDACTED]\nPrescription for [PERSON_REDACTED]\n\nDoliprane 1000mg - 3x daily\nAmoxicilline 500mg - 2x daily",
  "redacted_text": "Dr. [PERSON_REDACTED]\nPrescription for [PERSON_REDACTED]\n\nDoliprane 1000mg - 3x daily\nAmoxicilline 500mg - 2x daily",
  "phi_detected": true,
  "phi_entities": [
    {"type": "PERSON", "original": "Dr. Smith"},
    {"type": "PERSON", "original": "John Doe"}
  ],
  "medications": [
    {"name": "doliprane", "dosage": "1000mg"},
    {"name": "amoxicilline", "dosage": "500mg"}
  ],
  "total_medications": 2,
  "drug_alternatives": [
    {
      "original_drug": {"name": "doliprane", "dosage": "1000mg"},
      "drug_info": {
        "sources_found": ["Essential Medicines DB", "FDA API"],
        "alternatives": [
          {"generic_name": "paracetamol", "brand_names": ["Efferalgan", "Panadol"]}
        ],
        "text_from_llm": "Doliprane is a brand name for paracetamol..."
      }
    }
  ],
  "tools_used": ["azure_vision_ocr", "phi_filter", "vector_db_search"]
}
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "No module named 'sam2'"
```bash
cd backend/segment-anything-2
pip install -e .
```

#### 2. "Could not load vector database" (FAISS error with non-ASCII path)
This happens when your project folder contains special characters (é, è, etc.). The code automatically handles this by copying to a temp directory.

#### 3. "Azure Vision OCR not working"
- Check that `AZURE_VISION_ENDPOINT` and `AZURE_VISION_KEY` are set in `backend/.env`
- Verify your Azure resource is in the correct region
- Check Azure portal for API quota/limits

#### 4. "MedicationVectorDB: got unexpected keyword argument 'use_hub'"
Update to the latest `medication_vector_db.py` which supports the `use_hub` parameter.

#### 5. "HuggingFace download failed"
- Check your `HF_TOKEN` is valid
- Verify the repository exists and is accessible
- Check your internet connection

---

## 📊 Extended Database

The prescription scanner includes **200+ medications** from the Tunisian essential medicines list:

| Category | Count | Examples |
|----------|-------|----------|
| **Analgesics** | 25+ | Paracétamol, Tramadol, Morphine |
| **Antibiotics** | 40+ | Amoxicilline, Ciprofloxacine, Azithromycine |
| **Cardiovascular** | 30+ | Amlodipine, Atenolol, Lisinopril |
| **Antidiabetics** | 15+ | Metformine, Glibenclamide, Insuline |
| **Psychiatric** | 20+ | Diazepam, Halopéridol, Fluoxétine |
| **Respiratory** | 15+ | Salbutamol, Béclométhasone, Théophylline |
| **And more...** | 55+ | Various therapeutic categories |

---

## 🌐 Data Sources

| Source | Type | Purpose |
|--------|------|---------|
| **FAISS Vector DB** | Local/Cloud | Semantic medication search |
| **FDA OpenFDA API** | REST API | Drug labels, interactions, NDC codes |
| **NIH RxNorm API** | REST API | Normalized drug names, RxCUI codes |
| **OpenRouter (LLaMA)** | LLM API | AI-generated drug information |
| **HuggingFace Hub** | Cloud Storage | Model weights, vector database |
| **Azure Vision** | Cloud API | OCR for prescription images |

---

## 🔒 Security Notes

1. **Never commit `.env` files** - Add to `.gitignore`
2. **API keys are sensitive** - Use environment variables in production
3. **PHI data is redacted** - But original data is processed in memory
4. **HTTPS recommended** - For production deployments
5. **Rate limits apply** - Check API provider documentation

---

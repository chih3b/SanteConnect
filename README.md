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

# SanteConnect - AI Medication Assistant

AI-powered medication identification and information system for Tunisia.

## Features

- 🔍 **Instant Drug Lookup** - Get medication info in 0.01s
- 🖼️ **Image Recognition** - Identify medications from photos (0.5-2s)
- 💊 **Smart Comparisons** - Check if drugs can be substituted
- ⚠️ **Interaction Warnings** - Detect dangerous drug combinations
- 🔄 **Alternative Finder** - Find generic equivalents
- 🎯 **Symptom Search** - Find medications by symptom (fever, pain, etc.)

## Quick Start

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn main:app --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Visit http://localhost:3000

## Database

25 Tunisian medications with complete information:
- Doliprane, Paracétamol, Efferalgan (pain/fever)
- Aspirine, Kardégic (cardiovascular)
- Advil, Voltarène (anti-inflammatory)
- And more...

## Performance

| Query Type | Response Time | Method |
|------------|---------------|--------|
| Simple drug info | 0.01-3s | Fast path |
| Symptom search | 0.01s | Fast path |
| Comparisons | 15-30s | AI Agent |
| Image identification | 0.5-2s | OCR + Fast path |

## API Endpoints

- `GET /agent/query?query=<question>` - Ask any question
- `POST /agent/identify` - Upload image for identification
- `GET /fast/<drug_name>` - Ultra-fast drug lookup
- `GET /search/<query>` - Search medications
- `GET /stats` - Database statistics

## Example Queries

**Simple Queries (Instant)**
- "doliprane"
- "side effects of aspirine"
- "does doliprane help with fever"
- "what medicine for pain"

**Complex Queries (AI Agent)**
- "can i use doliprane instead of aspirine"
- "alternatives to doliprane"
- "interactions between advil and aspirine"

## Technology Stack

**Backend**
- FastAPI
- LangGraph (AI agent)
- Ollama (qwen2.5:1.5b)
- Tesseract OCR
- Python 3.9+

**Frontend**
- React 19
- Tailwind CSS
- shadcn/ui components

## Architecture

```
┌─────────────┐
│   Frontend  │ (React)
└──────┬──────┘
       │
┌──────▼──────┐
│  FastAPI    │
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
┌──▼──┐  ┌─▼────┐
│Fast │  │Agent │
│Path │  │(AI)  │
└──┬──┘  └─┬────┘
   │       │
   └───┬───┘
       │
  ┌────▼────┐
  │Database │
  │(JSON)   │
  └─────────┘
```

## Configuration

Edit `config.py`:

```python
MODEL_NAME = "qwen2.5:1.5b"  # AI model
ENABLE_AGENT_BYPASS = True   # Fast path
USE_DATABASE = False          # Use JSON (fast)
```

## Safety & Disclaimers

⚠️ **Important**: This system is for informational purposes only. Always consult a healthcare professional before making decisions about medications.

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.

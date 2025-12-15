# Doctor Assistant Backend (backendmariem)

AI-powered doctor assistant with appointments, email, and document processing.

## Features

- 🤖 AI Medical Assistant (Groq LLM - Llama 3.3 70B)
- 📅 Google Calendar Integration
- 📧 Gmail Email Sending
- 📄 Document OCR Processing
- 🧠 Explainable AI (XAI) for decision transparency

## Setup

### 1. Install Dependencies

```bash
cd backendmariem
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required:
- `GROQ_API_KEY`: Get from https://console.groq.com

Optional (for Google integration):
- Place `credentials.json` from Google Cloud Console
- Run once to generate OAuth tokens

### 3. Google Calendar & Gmail Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Calendar API and Gmail API
4. Create OAuth 2.0 credentials
5. Download as `credentials.json` and place in this folder
6. First run will open browser for authentication

### 4. Run the Server

```bash
python main.py
```

Server runs on port 8003 by default.

## API Endpoints

### Authentication
- `POST /auth/doctor/register` - Register new doctor
- `POST /auth/doctor/login` - Login doctor
- `GET /auth/doctor/me` - Get current doctor info
- `PUT /auth/doctor/profile` - Update profile

### AI Assistant
- `POST /api/assistant/chat` - Chat with AI
- `POST /api/assistant/upload` - Upload document
- `GET /api/assistant/session` - Get session info
- `GET /api/assistant/status` - Get assistant status

### Appointments
- `GET /api/appointments` - List appointments
- `GET /api/appointments/{id}` - Get appointment
- `DELETE /api/appointments/{id}` - Delete appointment

### XAI
- `GET /api/xai/metrics` - Get XAI metrics

## Port Configuration

| Service | Port |
|---------|------|
| Main SanteConnect API | 8000 |
| MediBot API | 8001 |
| Dr. Raif API | 8002 |
| Doctor Assistant API | 8003 |
| Frontend | 3000 |

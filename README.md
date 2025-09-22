# ex-GPT System

Korea Expressway Corporation AI System

## Quick Start

```bash
# 1. Organize folders (one time)
FINAL_ORGANIZE.bat

# 2. Start system
START.bat
```

## Project Structure

```
interim_report/
├── backend/        # Backend API server (port 8001)
├── frontend/       # Frontend web UI (port 5173)
├── admin/          # Admin panel
├── 188.해무.../    # CCTV image data
├── START.bat       # System starter
└── README.md       # This file
```

## System Components

### Backend
- **Location**: `backend/`
- **Port**: 8001
- **Tech**: FastAPI + Ollama
- **Model**: qwen3:8b
- **Features**: Image search, Text chat, Multimodal analysis

### Frontend
- **Location**: `frontend/`
- **Port**: 5173
- **Tech**: React + Vite
- **Features**: Chat UI, Image search UI

### Admin
- **Location**: `admin/`
- **Features**: System management

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/search/images` | POST | Search CCTV images |
| `/api/v1/chat` | POST | Text chat |
| `/api/v1/chat/multimodal` | POST | Multimodal chat |
| `/docs` | GET | API documentation |

## Usage

### Image Search
- Keywords: 해무, 안개, fog, mist, CCTV, weather
- Example: "Show fog images from highway"

### Text Chat
- General Q&A about Korea Expressway operations
- Context-aware conversations

## Requirements

- Windows 10+
- Python 3.10+
- Node.js 18+
- Ollama (auto-installed)
- 8GB+ RAM

## Troubleshooting

### Ollama not starting
```bash
ollama serve
```

### Port conflict
Edit `backend/.env`:
```
PORT=8002
```

### Frontend build error
```bash
cd frontend
npm install
npm run dev
```

## Support

Digital Planning Department  
Extension: 800-4552

---
*Korea Expressway Corporation Internal Use*

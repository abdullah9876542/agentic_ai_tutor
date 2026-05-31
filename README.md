# 🎓 Agentic AI Tutor

An autonomous, intelligent tutoring system powered by GPT-4o, LangGraph, and FastAPI.

---

## 📋 Project Phases

| Phase | Module | Status |
|-------|--------|--------|
| 1 | Auth & Project Setup | ✅ Complete |
| 2 | OCR Marksheet Upload | 🔜 Next |
| 3 | Analyzer Agent | 🔜 Upcoming |
| 4 | Career & Roadmap Agent | 🔜 Upcoming |
| 5 | Tutor Agent (LangGraph) | 🔜 Upcoming |
| 6 | Quiz Engine | 🔜 Upcoming |
| 7 | Streamlit Frontend Polish | 🔜 Upcoming |
| 8 | Notifications & Analytics | 🔜 Upcoming |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI + Python |
| Database | SQLite + SQLAlchemy |
| AI Agents | LangChain + LangGraph |
| LLM | OpenAI GPT-4o |
| OCR | Tesseract (pytesseract) |
| Password Security | bcrypt (passlib) |

---

## ⚙️ Setup Instructions

### 1. Prerequisites

Make sure you have the following installed:
- Python 3.10 or higher → https://www.python.org/downloads/
- Tesseract OCR (for Phase 2) → https://github.com/tesseract-ocr/tesseract

**Install Tesseract:**
- **Windows:** Download installer from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS:** `brew install tesseract`
- **Linux/Ubuntu:** `sudo apt install tesseract-ocr`

---

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd agentic_ai_tutor
```

---

### 3. Create a Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS/Linux
source venv/bin/activate
```

---

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` and fill in your values:

```env
OPENAI_API_KEY=sk-your-key-here        # Get from https://platform.openai.com
APP_SECRET_KEY=any-random-string       # Just type anything for local dev
FASTAPI_HOST=http://localhost:8000     # Leave as-is for local dev
DATABASE_URL=sqlite:///./data/tutor.db # Leave as-is
UPLOAD_DIR=uploads                     # Leave as-is
```

---

### 6. Run the Application

You need **two terminals** — one for the backend, one for the frontend.

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

You should see:
```
🚀 Starting Agentic AI Tutor API...
✅ Database tables ready
📖 Docs available at: http://localhost:8000/docs
```

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run frontend/app.py
```

Streamlit will open at: http://localhost:8501

---

### 7. Verify Everything Works

| URL | What you should see |
|-----|-------------------|
| http://localhost:8000 | `{"status": "online"}` |
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8501 | Streamlit login page |

---

## 📁 Project Structure

```
agentic_ai_tutor/
│
├── backend/
│   ├── main.py              ← FastAPI app
│   ├── database.py          ← SQLite setup
│   ├── models.py            ← DB table definitions
│   ├── schemas.py           ← Request/response validation
│   ├── auth/
│   │   ├── routes.py        ← /auth/register, /auth/login
│   │   └── utils.py         ← Password hashing
│   ├── agents/              ← AI agents (Phases 3-5)
│   ├── services/            ← Business logic (Phases 6-8)
│   ├── routes/              ← API routes (Phases 2-8)
│   └── ocr/                 ← OCR pipeline (Phase 2)
│
├── frontend/
│   ├── app.py               ← Streamlit entry point
│   ├── pages/               ← One file per page
│   └── utils/
│       └── api_client.py    ← All API calls
│
├── data/                    ← SQLite DB file (auto-created)
├── uploads/                 ← Marksheet uploads (auto-created)
├── .env                     ← Your config (never commit this)
├── .env.example             ← Template for team members
└── requirements.txt
```

---

## 🔌 API Endpoints (Phase 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check |
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login |
| GET | `/auth/me/{user_id}` | Get user info |

Full interactive docs: http://localhost:8000/docs

---

## 🚨 Common Issues

**`ModuleNotFoundError`** — Make sure your virtual environment is activated.

**`Cannot connect to backend`** in Streamlit — Make sure FastAPI is running on port 8000.

**`sqlite3.OperationalError`** — The `data/` folder will be created automatically on startup. If issues persist, run `mkdir data` manually.

**Tesseract not found** — Install Tesseract and make sure it's in your system PATH. Test with: `tesseract --version`

---

## 👥 Team

| Name | Reg No | Role |
|------|--------|------|
| Moiz | 62224 | Developer |
| Anzala | 63975 | Developer |
| Abdullah | 61230 | Developer |

**Supervisor:** Muhammad Irfan Anis — Senior Lecturer

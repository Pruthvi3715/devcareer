# DevCareer — Developer Career Intelligence System

AI-powered career audit platform that analyzes your GitHub repositories, provides code review, architecture mapping, career gap analysis, and a 90-day improvement roadmap.

**Built for DevClash 2026 • April 18-19, 2026**

---

## Features

- 🔍 **GitHub Repo Audit** — Clones and statically analyzes your top repos
- 🤖 **AI Code Review** — LLM-powered code review with specific findings (file + line)
- 🏗️ **Architecture Graph** — Interactive dependency graph with onboarding paths
- 📊 **Career Verdict** — Junior / Mid / Senior classification with evidence
- 📈 **Gap Analysis** — Skills blocking your promotion, ranked by career ROI
- 📅 **90-Day Roadmap** — Weekly improvement plan tailored to your audit
- 💼 **Market Intel** — Matching job roles and salary-unlock skills
- 💬 **AI Chat Coach** — RAG-powered chatbot that knows your audit data
- 📥 **Export** — Download reports as PDF or PowerPoint
- 🔐 **Auth** — JWT login/signup with profile management
- 🎮 **Demo Mode** — Enter `demo` as username to explore with sample data

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite 8, Tailwind CSS 4, React Router 7, Recharts, ReactFlow |
| Backend | Python 3.11+, FastAPI, SQLAlchemy + SQLite, ChromaDB |
| AI | Google Gemini 2.5 Flash (via OpenAI-compatible SDK) |
| Deployment | Vercel (frontend), Render/Railway (backend) |

---

## Quick Start (Local)

### Prerequisites
- **Node.js 18+** (for the Vite frontend)
- **Python 3.11+** (for the FastAPI backend)

### 1. Configure secrets

Copy the example env file and add your keys:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
- **`GEMINI_API_KEY`** — Get one at [aistudio.google.com](https://aistudio.google.com/)
- **`GITHUB_TOKEN`** — Optional, avoids GitHub rate limits

### 2. Start (recommended)

From `devcareer/` run:

```powershell
./start-all.ps1
```

### 3. Start (manual)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Open in browser
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

### 5. Try it
- Enter `demo` for the pre-loaded sample audit
- Or enter any GitHub username (e.g. `octocat`) for a live audit

---

## LLM Providers

The backend supports 4 LLM providers via the `LLM_PROVIDER` env var:

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| **Gemini** (default) | `GEMINI_API_KEY` | `gemini-2.5-flash` |
| **Groq** | `GROQ_API_KEY` | `openai/gpt-oss-120b` |
| **OpenRouter** | `OPENROUTER_API_KEY` | `anthropic/claude-sonnet-4-5` |
| **Ollama** (local) | `OLLAMA_BASE_URL` | `llama3.2` |

---

## Deploying

### Frontend → Vercel
1. Push to GitHub
2. Import repository in [vercel.com](https://vercel.com)
3. Set root directory to `frontend`
4. Framework preset: Vite
5. Add env var: `VITE_API_URL` = your deployed backend URL

### Backend → Render
1. Create a new Web Service on [render.com](https://render.com)
2. Set root directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `GEMINI_API_KEY`, `GITHUB_TOKEN`, etc.

---

## Project Structure

```
devcareer/
├── frontend/           # React + Vite SPA
│   ├── src/
│   │   ├── pages/      # LandingPage, AuditPage, CareerReportPage, etc.
│   │   ├── components/ # RepoScoreCard, VerdictBadge, ChatWidget, etc.
│   │   ├── context/    # AuthContext (JWT)
│   │   ├── hooks/      # useAuditPolling
│   │   └── utils/      # api.js, pdfExport, pptExport
│   └── vercel.json     # SPA routing for Vercel
├── backend/            # Python FastAPI
│   ├── routers/        # audit, report, auth, chat endpoints
│   ├── services/       # claude_engine, github_collector, arch_mapper, etc.
│   ├── models/         # Pydantic schemas + SQLAlchemy models
│   ├── cache/          # In-memory cache + demo data
│   └── .env.example    # Template for API keys
└── README.md
```

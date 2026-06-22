<div align="center">
  <h1>📜 ScholarAI</h1>
  <p><strong>AI-Powered Government Scheme Discovery & Recommendation Platform</strong></p>
  <p>
    <em>Built for USAII Global AI Hackathon 2026</em>
  </p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-00a393?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61dafb?logo=react" alt="React">
  <img src="https://img.shields.io/badge/LangGraph-1.2+-orange" alt="LangGraph">
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ecf8e?logo=supabase" alt="Supabase">
  <img src="https://img.shields.io/badge/pgvector-0.8+-blueviolet" alt="pgvector">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 🚀 Overview

**ScholarAI** is an AI-powered platform that helps citizens discover, compare, and apply for government schemes tailored to their unique profiles. It combines a **LangGraph agent pipeline**, **pgvector RAG search**, and a **local LLM (Qwen2.5:3B)** to analyze 1000+ Indian government schemes across all states and ministries.

### Why ScholarAI?

- **1000+ schemes** scraped from central & state government portals
- **Complex eligibility criteria** — income, category, state, gender, education level
- **AI-powered comparison** — LLM generates structured analysis side-by-side
- **What-if simulations** — tweak your profile and see eligibility change in real time

---

## ✨ Features

| Feature | Description |
|---|---|
| **🔍 RAG Search** | pgvector hybrid search (vector + trigram + full-text) on scheme embeddings |
| **✅ Eligibility Engine** | Rule-based filtering + LLM income verification + state guard |
| **⚖️ Smart Comparison** | LLM-scored comparison across 4 dimensions (eligibility, benefit, goal, complexity) |
| **📊 Decision Reports** | AI-written recommendation with key strengths, drawbacks, confidence score |
| **🔄 What-If Simulator** | Change income/education/category and see eligibility re-calculated |
| **🤖 LangGraph Pipeline** | 11-node agent workflow: context → plan → eligibility → retrieve → verify → compare → decide → explain |
| **👤 Profile Management** | Persistent profiles with auto-extraction from chat |
| **📄 Document Upload** | Parse Aadhaar/income certificates to auto-fill profile |
| **📺 YouTube Tutorials** | Fetches relevant scheme tutorial videos |

---

## 🧠 Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────────────┐
│   Frontend   │     │              ScholarAI Backend                  │
│  (React 19)  │────▶│                                                 │
│  Vite +      │     │  ┌──────────────────────────────────────────┐  │
│  Tailwind 4  │     │  │       LangGraph Agent Pipeline           │  │
└──────────────┘     │  │                                          │  │
                     │  │  1. context_agent       (intent + prof)  │  │
                     │  │  2. question_planner    (missing fields)  │  │
                     │  │  3. eligibility_agent   (rule filter)     │  │
                     │  │  4. llm_income_verifier (LLM re-check)   │  │
                     │  │  5. retrieval_agent     (vector search)   │  │
                     │  │  6. relevance_verifier  (LLM verify)     │  │
                     │  │  7. comparison_agent    (LLM compare)    │  │
                     │  │  8. decision_advisor    (LLM recommend)  │  │
                     │  │  9. action_planner      (steps)          │  │
                     │  │  10. explanation_agent  (fallback)       │  │
                     │  │  11. responsible_ai     (disclaimer)     │  │
                     │  └──────────────────────────────────────────┘  │
                     │                    │                           │
                     │  ┌─────────────────▼───────────────────────┐   │
                     │  │  3-Layer Cache (Memory → Redis → DB)    │   │
                     │  └─────────────────────────────────────────┘   │
                     │                    │                           │
                     │  ┌─────────────────▼───────────────────────┐   │
                     │  │  Database (PostgreSQL + pgvector)        │   │
                     │  │  schemes │ rules │ faq │ embeddings     │   │
                     │  │  profiles │ chat_history │ llm_jobs     │   │
                     │  │  + pgmq queues + pg_cron + pg_graphql   │   │
                     │  └─────────────────────────────────────────┘   │
                     └─────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
├── backend/                        # FastAPI backend
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point, routes, startup
│   │   ├── config.py               # Settings via env vars
│   │   ├── database.py             # SQLAlchemy models + init_db
│   │   ├── vector_store.py         # pgvector + hybrid search + embeddings
│   │   ├── cache.py                # 3-layer cache (mem → Redis → pgmq)
│   │   ├── text_preprocessor.py    # Text cleaning for scraped data
│   │   ├── agents/                 # LangGraph pipeline (11 nodes)
│   │   │   ├── graph.py            # StateGraph definition
│   │   │   ├── nodes.py            # All agent implementations
│   │   │   ├── state.py            # AgentState TypedDict
│   │   │   └── schemas.py          # Pydantic LLM I/O schemas
│   │   ├── services/               # Business logic
│   │   │   ├── ai_service.py       # Local LLM (Qwen2.5) wrapper
│   │   │   ├── scoring_service.py  # Hybrid scoring engine
│   │   │   ├── eligibility_service.py
│   │   │   ├── recommendation_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── scheme_service.py
│   │   │   ├── doc_intelligence.py # Document upload/Aadhaar parsing
│   │   │   └── youtube_service.py
│   │   ├── routes/
│   │   │   └── integration.py      # All v2 API endpoints
│   │   ├── ai/                     # v1 AI layer (legacy)
│   │   ├── api/                    # v1 routes (legacy)
│   │   ├── rag/                    # v1 RAG (legacy)
│   │   ├── pipeline/               # v1 pipeline (legacy)
│   │   ├── core/                   # v1 config (legacy)
│   │   └── db/                     # v1 DB (legacy)
│   ├── scripts/                    # SQL migrations
│   ├── tests/
│   ├── requirements.txt
│   ├── .env                        # Environment config
│   └── supabase/                   # Local Supabase config
│
├── frontend/                       # React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/                  # Login, Register, ProfileSetup,
│   │   │                           # Dashboard, Comparison, DecisionReport,
│   │   │                           # WhatIfSimulator
│   │   ├── components/             # UI components, chat, comparison, decision
│   │   ├── services/               # auth, chat, scheme, profile, decision APIs
│   │   ├── hooks/                  # useSchemes, useAuth
│   │   ├── context/                # AuthContext
│   │   ├── layouts/                # AuthLayout, DashboardLayout
│   │   └── lib/                    # Supabase client, Axios instance
│   ├── .env
│   └── package.json
│
├── data-engineering/               # Scraping & embedding pipeline
│   ├── scraped_schemes/            # ~1000 raw scheme JSON files
│   ├── normalizer.py / v2          # Normalize raw → DB schema
│   ├── batch_normalizer.py
│   ├── generate_embeddings.py      # gte-small embeddings (384d)
│   ├── bulk_insert.py              # Insert to Supabase
│   └── supabase/                   # Supabase project config
│
├── start_all.sh / .bat             # Launch backend + frontend
├── run_backend.sh / .bat
├── run_frontend.sh / .bat
└── requirements.txt                # Root-level legacy deps
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Uvicorn, SQLAlchemy 2.0 |
| **Frontend** | React 19, Vite 8, Tailwind CSS 4, React Router 7 |
| **Database** | PostgreSQL 17 + pgvector 0.8 (via Supabase local) |
| **Vector Search** | pgvector (cosine) + pg_trgm + tsvector hybrid search |
| **AI Pipeline** | LangGraph 1.2 (11-node StateGraph) |
| **LLM** | Qwen2.5:3B (local, GGUF Q4_K_M) via OpenAI-compatible API |
| **Embeddings** | thenlper/gte-small (384-dim, sentence-transformers) |
| **Auth** | Supabase GoTrue (local) |
| **Cache** | In-memory → Redis → PostgreSQL (3-tier) |
| **Async Jobs** | pgmq (PostgreSQL message queue) |
| **Analytics** | pg_cron, Prometheus metrics |
| **Container** | Docker (Supabase stack: 11 containers) |

---

## ⚡ Quick Start (Fresh Machine)

### Prerequisites

- Python 3.13+
- Node.js 22+
- Docker Desktop
- 8 GB+ RAM (for local LLM + Supabase)

### 1. Clone & Install

```bash
git clone <repo-url>
cd ScholarAI

# Backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Start Supabase Local (Database)

```bash
cd backend

# Start all Supabase services (PostgreSQL + pgvector + auth + storage)
supabase start
```

This starts 11 Docker containers including PostgreSQL 17 with pgvector, Kong (API gateway), GoTrue (auth), Storage, Realtime, and more.

### 3. Configure Environment

Copy the template:

```bash
cp backend/.env.template backend/.env
```

Edit `backend/.env`:
```env
# Local LLM endpoint (start separately, see step 5)
LOCAL_LLM_URL=http://localhost:12434/engines/v1
LOCAL_LLM_MODEL=docker.io/ai/qwen2.5:3B-Q4_K_M

# Supabase local PostgreSQL (auto-configured by supabase start)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=sb_publishable_<your-local-key>

# Embedding model (downloads on first run)
HF_TOKEN=hf_<your-huggingface-token>
EMBEDDING_DIM=384
EMBEDDING_MODEL=thenlper/gte-small
```

For the frontend, edit `frontend/.env`:
```env
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=sb_publishable_<your-local-key>
VITE_API_URL=http://localhost:8000/api
```

### 4. Run Database Migrations & Seed Data

```bash
# Run the unified migration (creates tables, indexes, functions, pgmq queues)
psql "$DATABASE_URL" -f backend/scripts/001_unified_supabase_migration.sql

# Restore the 1000+ scraped schemes from dump
psql "$DATABASE_URL" < backend/local_data_dump.sql
```

Or let the app auto-initialize (creates tables + seeds 2 sample schemes on first startup):
```bash
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. Start Local LLM (Qwen2.5:3B)

You need a local LLM server (LocalAI, Ollama, or llama.cpp) serving an OpenAI-compatible API:

```bash
# Example with LocalAI:
docker run -p 12434:8080 \
  -v $PWD/models:/build/models \
  localai/localai:latest
# Then download Qwen2.5:3B-Q4_K_M.gguf into models/
```

### 6. Start the Application

**Option A — Launch scripts:**
```bash
./start_all.sh
```

**Option B — Manual:**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 7. Verify

```
Backend:   http://localhost:8000/api/health  → {"status":"healthy"}
Frontend:  http://localhost:5173              → Login page
API Docs:  http://localhost:8000/docs         → Swagger UI
```

---

## 📡 API Endpoints

### Profiles
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/profile` | Get current profile |
| `POST` | `/api/profile` | Create profile |
| `PUT` | `/api/profile` | Update profile |

### Schemes
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/schemes` | List/search schemes (supports `?search=&state=&category=`) |
| `GET` | `/api/schemes/recommended` | Top 10 eligible schemes for profile |
| `GET` | `/api/schemes/{id}` | Scheme details + rules + FAQs |
| `POST` | `/api/schemes/search` | Hybrid search (vector + trigram + full-text) |
| `POST` | `/api/schemes/compare` | LLM-powered comparison (up to 10) |
| `POST` | `/api/schemes/simulate` | What-if eligibility simulation |

### Chat & AI
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | LangGraph pipeline (context → eligibility → retrieve → compare → decide → explain) |
| `GET` | `/api/chat/history` | Get chat history for session |

### Other
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/decision-report` | Generate decision report for a scheme |
| `POST` | `/api/document-upload` | Upload Aadhaar/income certificate |
| `POST` | `/api/feedback` | Submit feedback on recommendations |
| `GET` | `/api/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |

---

## 📋 Example Usage

```bash
# Health check
curl http://localhost:8000/api/health

# Get recommended schemes for anonymous user
curl http://localhost:8000/api/schemes/recommended

# Create/update profile
curl -X PUT http://localhost:8000/api/profile \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Rajesh","state":"Karnataka","annual_income":250000,"category":"OBC","education_level":"Graduate","student":true}'

# Chat with AI (triggers LangGraph pipeline)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "session-id: test-123" \
  -d '{"query":"I am an OBC student from Karnataka looking for scholarships"}'

# Compare schemes
curl -X POST http://localhost:8000/api/schemes/compare \
  -H "Content-Type: application/json" \
  -d '{"scheme_ids":[1,2,3]}'
```

---

## 🔌 Requirements Per Machine

| Component | Required | Notes |
|---|---|---|
| Docker Desktop | ✅ Yes | Runs 11 Supabase containers (PostgreSQL + pgvector + auth + storage) |
| Python 3.13+ | ✅ Yes | With pip |
| Node.js 22+ | ✅ Yes | With npm |
| Local LLM server | ✅ Yes | Qwen2.5:3B on port 12434 (LocalAI / Ollama / llama.cpp) |
| HuggingFace token | ✅ Yes | To download `thenlper/gte-small` embedding model |
| RAM | 8 GB+ | ~4 GB for Supabase + ~2 GB for LLM + ~1 GB for app |
| Disk | 10 GB+ | ~3 GB for Docker images + ~2 GB for LLM model + ~1 GB for embeddings |
| Internet | First run only | For Docker pulls, pip installs, model downloads |

---

## 🧪 How It Works

### LangGraph Agent Pipeline (11 nodes)

```mermaid
flowchart LR
    A[User Query] --> B[context_agent]
    B --> C[question_planner]
    C --> D[eligibility_agent]
    D --> E[llm_income_verifier]
    E --> F[retrieval_agent]
    F --> G{relevance_verifier}
    G -- low score --> F
    G -- high score --> H[comparison_agent]
    H --> I[decision_advisor]
    I --> J[action_planner]
    J --> K[explanation_agent]
    K --> L[responsible_ai_layer]
    L --> M[Response]
```

### Scoring System

| Dimension | Weight | Source |
|---|---|---|
| Eligibility | 40% | Rule-based (income, category, state, gender, education) |
| Benefit Value | 25% | LLM evaluates financial amount, coverage, frequency |
| Goal Alignment | 25% | LLM matches scheme category to user goals/education |
| Complexity | 10% | Number of steps, documents required |

---

## 🧰 Development

### Code Style
```bash
pip install black ruff mypy
black backend/
ruff check backend/
```

### Testing
```bash
cd backend
pytest -v
```

### Data Pipeline (Re-scrape & Re-embed)
```bash
cd data-engineering
python batch_normalizer.py           # Normalize raw JSON → normalized_schemes.json
python generate_embeddings.py        # gte-small → schemes_with_embeddings.json
python bulk_insert.py                # Insert to Supabase
```

---

## 🚧 Roadmap

- [x] LangGraph 11-node agent pipeline
- [x] pgvector hybrid search (vector + trigram + text)
- [x] 1000+ scraped Indian government schemes
- [x] Local LLM (Qwen2.5:3B) inference
- [x] React frontend (Dashboard, Comparison, Simulator, Chat)
- [x] Supabase Auth + PostgreSQL + Storage
- [x] Document upload / Aadhaar parsing
- [x] What-if simulator
- [ ] Multi-language support (Hindi + regional)
- [ ] Scheme scraping auto-refresh (cron)
- [ ] Admin panel for scheme management
- [ ] Mobile app (React Native)

---

## 🤝 Contributing

Built for the **USAII Global AI Hackathon 2026**. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <p>
    Built with ❤️ for the <strong>USAII Global AI Hackathon 2026</strong>
  </p>
  <p>
    <em>Empowering citizens through AI-driven scheme discovery</em>
  </p>
</div>

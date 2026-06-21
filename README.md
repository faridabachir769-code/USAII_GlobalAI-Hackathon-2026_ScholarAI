<div align="center">
  <h1>📜 ScholarAI</h1>
  <p><strong>AI-Powered Government Scheme Discovery & Recommendation Platform</strong></p>
  <p>
    <em>Built for USAII Global AI Hackathon 2026</em>
  </p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-00a393?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0+-red" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4-412991?logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ecf8e?logo=supabase" alt="Supabase">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 🚀 Overview

**ScholarAI** is an intelligent backend platform that helps citizens discover, compare, and apply for government schemes tailored to their unique profiles. Using a combination of **rule-based eligibility filtering**, **vector similarity search (RAG)**, and **LLM-powered analysis**, ScholarAI bridges the gap between citizens and the welfare schemes they qualify for.

### Why ScholarAI?

- **Hundreds of schemes**, scattered across departments, states, and categories — citizens don't know what they're eligible for.
- **Complex eligibility criteria** — income limits, age restrictions, state-specific rules, category reservations.
- **No unified comparison tool** — users can't easily weigh options side by side.

ScholarAI solves all of this with a clean, API-first approach.

---

## ✨ Features

| Feature | Description |
|---|---|
| **🔍 Scheme Discovery** | RAG-based vector search finds schemes semantically related to user profiles |
| **✅ Eligibility Check** | Rule-based filtering (state, age, income, category) with detailed reasoning |
| **⚖️ Smart Comparison** | Compare 2+ schemes side-by-side with LLM-generated analysis |
| **📊 Decision Reports** | AI-powered ranking with weighted scoring, tradeoffs, and recommendations |
| **👤 Profile Management** | CRUD for user profiles with full validation |
| **🔌 Supabase Ready** | Built for PostgreSQL on Supabase with connection pooler support |

---

## 🧠 Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────────┐
│   Frontend   │     │              ScholarAI API                  │
│  (Any HTTP)  │────▶│                                             │
└──────────────┘     │  ┌──────────┐  ┌────────────┐  ┌─────────┐ │
                     │  │ Profile  │  │ Eligibility│  │Decision │ │
                     │  │  Routes  │  │  Routes    │  │ Report  │ │
                     │  └────┬─────┘  └──────┬─────┘  └────┬────┘ │
                     │       │               │              │      │
                     │  ┌────▼───────────────▼──────────────▼────┐ │
                     │  │          Recommendation Pipeline       │ │
                     │  │                                        │ │
                     │  │  ┌─────────┐  ┌──────────┐  ┌───────┐ │ │
                     │  │  │Retriever│─▶│Eligibility│─▶│Decision│ │ │
                     │  │  │  (RAG)  │  │  Service  │  │ Engine│ │ │
                     │  │  └────┬────┘  └──────────┘  └───┬───┘ │ │
                     │  │       │                          │     │ │
                     │  │  ┌────▼──────────────────────────▼───┐ │ │
                     │  │  │     LLM Analysis Layer           │ │ │
                     │  │  │  (Comparison + Explanation)      │ │ │
                     │  │  └──────────────────────────────────┘ │ │
                     │  └───────────────────────────────────────┘ │
                     │                    │                       │
                     │  ┌─────────────────▼───────────────────┐  │
                     │  │          Database (SQL/PostgreSQL)   │  │
                     │  │  profiles │ schemes │ comparisons    │  │
                     │  └─────────────────────────────────────┘  │
                     └────────────────────────────────────────────┘
```

### System Flow

```mermaid
flowchart LR
    A[User Profile] --> B[RAG Retriever]
    B --> C[Vector Search]
    C --> D[Eligibility Rules]

    D --> E[Decision Engine]
    E --> F[LLM Analysis]
    F --> G[Comparison Report]

    D --> H[Eligible Schemes]
    E --> I[Ranked Results]
    F --> J[AI Explanation]

    G --> K[Final Response]
    H --> K
    I --> K
    J --> K
```

---

## 🗂️ Project Structure

```
backend/
├── app/
│   ├── ai/                          # AI/LLM layer
│   │   ├── llm_service.py           # OpenAI GPT wrapper
│   │   ├── comparison_analyzer.py   # Scheme comparison via LLM
│   │   └── decision_engine.py       # Weighted scoring & ranking
│   │
│   ├── api/                         # FastAPI route handlers
│   │   ├── profiles.py              # CRUD for user profiles
│   │   ├── eligibility.py           # Eligibility check endpoint
│   │   ├── comparison.py            # Scheme comparison endpoint
│   │   ├── decision_report.py       # Decision report endpoint
│   │   └── schemas.py               # Pydantic request/response models
│   │
│   ├── core/                        # Core configuration
│   │   ├── config.py                # Settings via Pydantic (env vars)
│   │   └── logger.py                # Centralized logging
│   │
│   ├── db/                          # Database layer
│   │   ├── base.py                  # Engine, session, init_db()
│   │   └── models.py                # SQLAlchemy ORM models
│   │
│   ├── pipeline/                    # Orchestration
│   │   └── recommendation.py        # End-to-end recommendation pipeline
│   │
│   ├── rag/                         # Retrieval-Augmented Generation
│   │   ├── embedding.py             # OpenAI embedding generation
│   │   ├── vector_search.py         # pgvector similarity search
│   │   └── retriever.py             # Orchestrates embedding + search
│   │
│   ├── rules/                       # Rule definitions (extensible)
│   │   └── __init__.py
│   │
│   └── services/                    # Business logic
│       ├── profile_service.py       # Profile CRUD operations
│       ├── scheme_service.py        # Scheme data access
│       ├── eligibility_service.py   # Rule-based eligibility filtering
│       └── recommendation_service.py# Orchestrates comparisons & reports
│
├── run.py                           # Entry point (uvicorn)
├── requirements.txt                 # Dependencies
└── .env                             # Configuration (not committed)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | FastAPI (Python 3.13+) |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | SQLite (dev) / PostgreSQL + pgvector (production) |
| **Hosting** | Supabase (PostgreSQL + connection pooling) |
| **AI / LLM** | OpenAI GPT-4, text-embedding-3-small |
| **Vector Search** | pgvector (cosine distance) |
| **Validation** | Pydantic v2 |
| **Server** | Uvicorn with hot-reload |

---

## ⚡ Quick Start

### Prerequisites

- Python 3.13+
- pip
- OpenAI API key (for LLM features)

### 1. Clone & Install

```bash
git clone <repo-url>
cd ScholarAI

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

Create `backend/.env`:

```env
# Database — SQLite for local dev (default)
DATABASE_URL=sqlite:///./test.db

# Or Supabase PostgreSQL production
# DATABASE_URL=postgresql://postgres:password@db.<ref>.supabase.co:5432/postgres

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=True

# OpenAI (required for AI features)
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run the Server

```bash
cd backend
python run.py
```

The API will be available at **http://localhost:8000**  
Interactive docs at **http://localhost:8000/docs** (Swagger UI)

---

## 📡 API Endpoints

### 👤 Profile Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/profile` | Create a new profile |
| `GET` | `/api/profile/{id}` | Get profile by ID |
| `PUT` | `/api/profile/{id}` | Update profile |
| `GET` | `/api/profiles` | List all profiles (paginated) |

### ✅ Eligibility

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/eligibility` | Check which schemes a profile is eligible for |

### ⚖️ Comparison

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/compare` | Compare 2+ schemes for a profile (AI-powered) |

### 📊 Decision Report

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/decision-report` | Generate comprehensive decision report with ranking |

### 🏥 Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API root info |
| `GET` | `/health` | Health check |

---

## 📋 Example Usage

### Create a Profile

```bash
curl -X POST http://localhost:8000/api/profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rajesh Kumar",
    "age": 25,
    "state": "Karnataka",
    "income": 150000,
    "occupation": "Student",
    "education_level": "Bachelor'\''s",
    "category": "General",
    "goals": "Education funding for higher studies"
  }'
```

### Check Eligibility

```bash
curl -X POST http://localhost:8000/api/eligibility \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "<profile-uuid>"}'
```

### Compare Schemes

```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "<profile-uuid>",
    "scheme_ids": ["<scheme-uuid-1>", "<scheme-uuid-2>"]
  }'
```

---

## 🔌 Supabase Setup (Production)

1. **Create a Supabase project** at [supabase.com](https://supabase.com)
2. **Get your connection string** from Project Settings → Database
3. **Enable pgvector** (if using vector search):
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. **Set DATABASE_URL** in `.env`:
   ```env
   # Direct connection (IPv6 required)
   DATABASE_URL=postgresql://postgres:password@db.<ref>.supabase.co:5432/postgres

   # Or via connection pooler (IPv4)
   DATABASE_URL=postgresql://postgres.<ref>:password@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
   ```

---

## 🧪 How It Works

```mermaid
sequenceDiagram
    participant User
    participant API as ScholarAI API
    participant RAG as RAG Retriever
    participant Rules as Eligibility Service
    participant Engine as Decision Engine
    participant LLM as AI Layer
    participant DB as Database

    User->>API: POST /eligibility (profile_id)
    API->>RAG: Retrieve similar schemes
    RAG->>DB: Fetch profile + schemes
    RAG->>RAG: Generate profile embedding
    RAG->>RAG: Vector similarity search
    RAG-->>API: Schemes with scores

    API->>Rules: Filter by eligibility rules
    Rules->>Rules: Check state, age, income, category
    Rules-->>API: Eligible schemes

    alt Comparison Requested
        API->>Engine: Score & rank schemes
        Engine-->>API: Ranked results with breakdown
        API->>LLM: Generate comparison analysis
        LLM-->>API: Structured comparison text
    end

    API-->>User: Eligibility / Comparison / Report
```

### Key Components

- **Retriever** — Creates a text embedding of the user profile using OpenAI's `text-embedding-3-small`, then performs a pgvector cosine similarity search against all scheme embeddings.
- **Eligibility Service** — Applies deterministic rules: state availability, age range, income threshold, and category matching. Returns clear eligibility reasons for each scheme.
- **Decision Engine** — Scores each eligible scheme across four weighted dimensions:
  - `eligibility_score` (40%) — How well the scheme's criteria match the profile
  - `benefit_score` (25%) — Quality and relevance of benefits
  - `goal_alignment_score` (25%) — How well the scheme aligns with user goals
  - `complexity_score` (10%) — Inverse of application difficulty
- **LLM Layer** — GPT-4 provides natural-language comparison analysis, highlighting benefits, drawbacks, application ease, and processing time tradeoffs.

---

## 🧰 Development

### Code Style

```bash
# Install dev dependencies
pip install black ruff mypy

# Format code
black backend/

# Lint
ruff check backend/
```

### Testing

```bash
cd backend
pytest -v
```

---

## 📁 Database Schema

```mermaid
erDiagram
    profiles {
        uuid id PK
        string name
        int age
        string state
        int income
        string occupation
        string education_level
        string category
        text goals
        datetime created_at
        datetime updated_at
    }

    schemes {
        uuid id PK
        string scheme_name
        string category
        string state
        text description
        text benefits
        text eligibility
        jsonb documents
        jsonb application_steps
        string apply_url
        json embedding
        datetime created_at
        datetime updated_at
    }

    scheme_comparisons {
        uuid id PK
        uuid profile_id FK
        jsonb scheme_ids
        jsonb report
        datetime created_at
    }

    profiles ||--o{ scheme_comparisons : has
    schemes ||--o{ scheme_comparisons : included_in
```

---

## 🚧 Roadmap

- [x] Profile CRUD with full validation
- [x] Rule-based eligibility filtering
- [x] RAG-based vector search (OpenAI + pgvector)
- [x] Weighted decision engine scoring
- [x] LLM-powered scheme comparison
- [x] Supabase PostgreSQL integration
- [ ] Scheme data seeding scripts
- [ ] Frontend dashboard
- [ ] Multi-language support
- [ ] User authentication & authorization
- [ ] Admin panel for scheme management
- [ ] Analytics & reporting

---

## 🤝 Contributing

This project was built for the **USAII Global AI Hackathon 2026**. Contributions, ideas, and feedback are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
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

# ScholarAI — RAG & LLM Pipeline Architecture

## Overview

ScholarAI uses a **multi-stage RAG (Retrieval-Augmented Generation) pipeline** powered by LangGraph to match Indian government welfare scheme seekers with the right schemes. The system combines **vector search**, **structured DB filtering**, **LLM reasoning**, and **semantic education matching** to produce grounded, accurate recommendations.

The pipeline runs as a **10-node LangGraph** — a DAG where each node is an async Python function and conditional edges allow retry loops.

---

## 1. Data Pipeline: Chunking, Embedding & Storage

### 1.1 Source Data

Scheme data is scraped from government portals (NSP, state portals, PM websites) and stored in PostgreSQL:

| Table | Schema | Purpose |
|---|---|---|
| `schemes` | `(id, name, benefits, eligibility_text, documents_required, application_process, ministry, state, ...)` | Scheme master data |
| `rules` | `(scheme_id, income_max, categories_allowed, states_allowed, gender_allowed, education_level, student_required)` | Eligibility rules |
| `faq` | `(scheme_id, question, answer)` | FAQ knowledge base |
| `scheme_embeddings` | `(scheme_id, chunk_index, section, content, embedding vector(384))` | Vector storage |
| `profiles` | `(user_id, profile_data JSONB)` | User demographic profiles |
| `chat_history` | `(session_id, role, content, created_at)` | Conversation persistence |
| `user_scheme_matches` | `(user_id, scheme_id, match_score, match_reasons, refreshed_at)` | Persisted match cache |

### 1.2 Chunking Strategy

Each scheme's text content is **chunked** into overlapping segments for embedding:

- **Section-based splitting**: Benefits, Eligibility, Documents, Process each become separate chunks
- **Sliding window**: Long sections (>512 chars) are split with 128-char overlap
- **Chunk metadata**: Each chunk stores `scheme_id`, `chunk_index`, `section` (benefits/eligibility/docs/process)

Chunking happens during the `embed_schemes.py` indexing script:

```python
def chunk_scheme(scheme) -> list[dict]:
    chunks = []
    for section in ["benefits", "eligibility_text", "documents_required", "description"]:
        text = getattr(scheme, section, "")
        if not text:
            continue
        # Split long sections with overlap
        words = text.split()
        if len(words) <= 200:
            chunks.append({"text": text, "section": section})
        else:
            for i in range(0, len(words), 150):
                segment = " ".join(words[i:i+200])
                chunks.append({"text": segment, "section": section})
    return chunks
```

### 1.3 Embedding Model

| Property | Value |
|---|---|
| **Model** | `thenlper/gte-small` |
| **Dimension** | 384 |
| **Normalization** | L2-normalized (cosine similarity) |
| **Device** | CUDA if available, else CPU |
| **Source** | `sentence-transformers` (PyTorch) |

**Prefix convention** (OpenAI-compatible):
- Query: `"query: {user_query}"`
- Passage: `"passage: {chunk_text}"`

This improves retrieval by matching the training distribution of GTE.

### 1.4 Vector Storage — pgvector

Embeddings are stored in the `scheme_embeddings` table with a `vector(384)` column. Two indexes are maintained:

```sql
-- HNSW (primary, fast approximate nearest neighbor)
CREATE INDEX idx_scheme_embeddings_hnsw ON scheme_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- IVFFlat (fallback)
CREATE INDEX idx_scheme_embeddings_ivfflat ON scheme_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

- **HNSW** is the default index — it provides ~10x faster search than IVFFlat with better recall
- `IVFFlat` serves as a fallback (some Supabase plans don't support HNSW yet)

---

## 2. Retrieval Strategy

### 2.1 Three Retrieval Modes

| Mode | When Used | Method |
|---|---|---|
| **pgvector only** | When `scheme_ids` filter is set (within pipeline) | Cosine similarity search over `scheme_embeddings` |
| **Hybrid search** | API search endpoint (`/api/schemes/search`) | Vector + trigram + full-text combined |
| **FAQ lookup** | On every pipeline run | Batch SQL query `WHERE scheme_id IN (...)`

### 2.2 pgvector Search

```sql
SELECT se.id, se.scheme_id, se.content,
       1 - (se.embedding <=> :query_vec) AS similarity
FROM scheme_embeddings se
WHERE 1 - (se.embedding <=> :query_vec) > :threshold
  AND se.scheme_id IN :scheme_ids     -- optional filter
ORDER BY se.embedding <=> :query_vec
LIMIT :limit
```

- Uses **cosine distance** (`<=>` operator)
- `threshold` default: `0.55` (configurable via `VECTOR_SEARCH_THRESHOLD`)
- `limit` default: `20` (configurable via `VECTOR_SEARCH_LIMIT`)
- `ivfflat.probes` set to `20` for quality-speed tradeoff

### 2.3 Hybrid Search (for ad-hoc queries)

The PostgreSQL function `search_schemes_hybrid()` combines three signals:

```
combined_score = 0.5 × vec_score + 0.3 × trigram_score + 0.2 × text_score
```

| Signal | Weight | Source |
|---|---|---|
| Vector cosine similarity | 0.5 | `scheme_embeddings` |
| Trigram similarity | 0.3 | `similarity(scheme.name, query)` via `pg_trgm` |
| Full-text rank | 0.2 | `ts_rank(scheme.search_vector, query)` |

### 2.4 Query Rewriting

Before vector search, the user's query is **rewritten** by an LLM into a keyword-dense search query:

```
Input:  "I'm an OBC student in Bihar with 2.5 lakh income, any scholarships?"
Output: "OBC student Bihar 2.5 lakh income scholarship financial assistance government scheme eligibility"
```

This improves retrieval precision because the embedding model matches keyword-dense queries better than conversational ones.

### 2.5 MMR Diversity Selection

Retrieved chunks are deduplicated per scheme using **Maximal Marginal Relevance (MMR)**:

```python
def _mmr_select(results, lambda_param=0.5, max_results=6):
    # lambda_param: 0.5 balances relevance vs diversity
    # For each scheme, select max_results chunks that are
    # both relevant AND diverse from each other
```

This ensures the top-6 chunks per scheme cover different aspects (benefits, eligibility, process) rather than all being near-identical.

---

## 3. LangGraph Pipeline (10 Nodes)

### 3.1 Pipeline Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. context_agent      — Intent detection (browse vs personalize)    │
│                          + Profile extraction (LLM + regex)        │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. question_planner   — Identify missing profile fields to ask      │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. eligibility_agent  — SQL rules filtering + education embedding   │
│                          + state guard                              │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. llm_income_verifier — LLM re-verifies income against raw text   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. retrieval_agent    — FAQ batch load + Vector search + MMR       │
│                          + YouTube tutorial fetch                   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. relevance_verifier — Score check + LLM verification             │
│                          ← conditional: retry if low score         │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. comparison_agent   — Generates structured comparison data       │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. decision_advisor   — LLM generates recommendation text          │
│                          (cites state, income, category)           │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 9. action_planner     — 6-step document/application action plan    │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│10. explanation_agent  — Build grounded response if LLM unavailable │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│11. responsible_ai_layer — Disclaimer + confidence score            │
└─────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
               Final Response (markdown)
```

### 3.2 Node Details

#### Node 1: `context_agent`
- **Intent detection**: Scores query for browse vs personalization keywords
- **Browse mode**: Regex-based extraction of state/category/gender/education/income
- **Personalize mode**: LLM extraction via `generate_structured_json` with `ProfileExtraction` schema
- **Full state names** matched: all 28 Indian states + National

#### Node 2: `question_planner`
- Checks which profile fields are missing/incomplete
- Returns `missing_fields` array (used by frontend to prompt user)
- Browse mode only asks for state + category

#### Node 3: `eligibility_agent`
- Queries all `Scheme` + `Rule` from DB
- **Browse mode**: Relaxed — checks only state + category
- **Personalize mode**: Full check — student, income, category, state, gender, education, disability
- **Education semantic matching**: Uses `education_semantic_match()` — first tries a known mapping dictionary (10th→School, 12th→HigherSecondary, B.Tech→Engineering, etc.), then falls back to **embedding cosine similarity** with threshold 0.55
- **State guard**: Double-check — both `rules.states_allowed` AND `scheme.state` must match user state
- **Reason tracking**: Each passing criterion adds a human-readable match_reason

#### Node 4: `llm_income_verifier`
- LLM re-verifies income limits by reading raw `eligibility_text`
- Removes schemes where eligibility text says "income below ₹1 lakh" but user earns ₹8 lakh
- Only runs when >2 schemes matched (small sets are deterministic)

#### Node 5: `retrieval_agent`
- **FAQ batch**: Single SQL query `WHERE scheme_id IN (...)` for all matched schemes
- **Query rewrite**: LLM rewrites user query → keyword-dense search query
- **Vector search**: `search_similar_documents()` with `scheme_ids` filter
- **MMR diversity**: Selects diverse chunks per scheme with λ=0.5
- **State guard**: Skips vector results where scheme state ≠ user state
- **YouTube**: Fetches tutorial videos via YouTube API for top 3 schemes

#### Node 6: `relevance_verifier`
- Computes average relevance score from retrieved docs
- Checks if query keywords appear in scheme names/benefits
- **LLM verification**: Asks LLM to verify each matched scheme against the user's actual profile, removes false positives
- **Conditional retry**: If score < threshold and retries remain, expands query with generic welfare terms and loops back to retrieval_agent

#### Node 7: `comparison_agent`
- For 1 scheme: returns single comparison entry
- For 2+ schemes: **LLM generates full comparison** with financial_benefit, eligibility_difficulty, required_documents_count, processing_time, approval_likelihood, goal_alignment
- **Grounded constraint**: "Base ALL fields on the provided data — do not guess or fabricate"

#### Node 8: `decision_advisor`
- **Browse mode**: Clean list with breakdown (state vs central, top ministries)
- **Personalize mode**: LLM generates 2-3 paragraph recommendation
- Groups FAQ + embedding chunks by scheme_id for rich context
- **State citation**: Prompt explicitly includes `"Since you are a resident of {state}, you may qualify..."`

#### Node 9: `action_planner`
- Generates 6-step action plan: Gather Documents → Visit Portal → Apply → Upload → Submit & Track → Follow Up
- Uses real `documents_required` field from scheme data

#### Node 10: `explanation_agent`
- **Grounded fallback**: If decision_advisor failed, builds response from actual scheme data
- Shows recommended scheme with real benefits, eligibility, documents
- Lists other matched schemes with match reasons
- Includes FAQ context and action plan

#### Node 11: `responsible_ai_layer`
- Appends disclaimer: "This is AI-generated analysis, does not guarantee eligibility"
- Replaces "you qualify" → "you may qualify" throughout
- Computes confidence score based on completed profile fields

---

## 4. Education Semantic Matching

### 4.1 Problem

Users say "I'm in 12th" but schemes list "HigherSecondary" as requirement.
Simple string matching would miss this match.

### 4.2 Solution — Two-Stage Matching

```
                    ┌──────────────┐
User Education ────→│ Known Mapping│
                    └──────┬───────┘
                           │
                    matched? ──yes──→ MATCH
                           │
                           no
                           ▼
                    ┌──────────────┐
                    │  Embedding   │
                    │  Similarity  │
                    └──────┬───────┘
                           │
                    sim ≥ 0.55? ──yes──→ MATCH
                           │
                           no
                           ▼
                        NO MATCH
```

### 4.3 Known Mapping Dictionary

```python
KNOWN_MAP = {
    "10th": "school", "ssc": "school", "matric": "school",
    "12th": "highersecondary", "hsc": "highersecondary", "intermediate": "highersecondary",
    "b.tech": "engineering", "b.e": "engineering", "be": "engineering",
    "b.sc": "graduate", "b.a": "graduate", "b.com": "graduate", "bachelor": "graduate",
    "m.sc": "postgraduate", "m.a": "postgraduate", "master": "postgraduate",
    "m.tech": "postgraduate", "m.e": "postgraduate",
    "ph.d": "phd", "phd": "phd", "doctoral": "phd",
    "iti": "diploma", "polytechnic": "diploma",
}
```

### 4.4 Embedding Fallback

When no dictionary entry exists, both terms are embedded with the same GTE model used for chunk retrieval:

```python
u_emb = get_embedding("school")      # 384-dim vector
r_emb = get_embedding("highersecondary")
sim = cosine_similarity(u_emb, r_emb)  # ≈ 0.72
if sim >= 0.55: match  # threshold tuned on test data
```

Results are cached in-memory (`_EDUCATION_SEM_CACHE`) to avoid repeated embedding calls.

---

## 5. State Exclusivity Guard

### 5.1 Problem

A user from Maharashtra should NOT see Tamil Nadu state schemes. But data quality issues can cause schemes to have:
- `rules.states_allowed = "Maharashtra, National"` (incorrectly includes "National")
- `scheme.state = "National"` when it's actually state-specific

### 5.2 Two-Layer Guard

```
Layer 1: Rules Check                    Layer 2: Scheme State
─────────────────────────────           ─────────────────────────────
rules.states_allowed checks             scheme.state vs user.state
user_state in allowed OR                If both are non-national and
"National" in allowed                   different → EXCLUDE
                                        (catches incorrect National)
```

Applied in both:
- `eligibility_agent` (Python rules iteration)
- `retrieval_agent` (vector result filtering)
- `get_eligible_schemes()` SQL function (DB-side)

---

## 6. LLM Integration

### 6.1 Model

| Property | Value |
|---|---|
| **Model** | `Qwen2.5:3B` (GGUF Q4_K_M quantized) |
| **Serving** | Ollama / LocalAI compatible OpenAI API |
| **Endpoint** | `POST /v1/chat/completions` |
| **Temperature** | 0.1 (low for structured output) |
| **Max tokens** | 4096 |
| **Timeout** | 30 seconds |

### 6.2 When LLM is Called

| Call | Schema | Purpose |
|---|---|---|
| `context_agent` | `ProfileExtraction` | Extract state, income, category from query |
| `retrieval_agent` | `SearchQueryRewrite` | Rewrite query for vector search |
| `llm_income_verifier` | `IncomeVerificationResult` | Verify income against raw eligibility text |
| `relevance_verifier` | Dynamic schema | Verify scheme-vs-profile match quality |
| `comparison_agent` | `ComparisonItem[]` | Generate structured comparison |
| `decision_advisor` | Free text | Generate recommendation paragraph |

### 6.3 Structured JSON Output

All LLM calls go through `generate_structured_json()` which:
1. Builds a system prompt with `model_json_schema()` field definitions
2. Sends request with `response_format: {"type": "json_object"}` (OpenAI-compatible)
3. Parses and validates response through Pydantic
4. Falls back to regex JSON extraction if validation fails

### 6.4 Adaptive Prompting

Prompts adapt based on context:
- Fewer matched schemes → shorter prompts
- High income → "Most schemes likely qualify"
- Retry → broader search with more welfare keywords

---

## 7. Caching & Storage

### 7.1 Three-Layer Cache

```
    ┌──────────┐
    │  Memory  │  ← dict (fast, per-process, lost on restart)
    ├──────────┤
    │  Redis*  │  ← shared across processes (optional, via settings)
    ├──────────┤
    │ Postgres │  ← persistent (always available)
    └──────────┘
```

*Redis is optional — the system degrades gracefully to memory-only.

### 7.2 Persistence

| Data | Table | Key |
|---|---|---|
| User profile | `profiles` | `user_id` (unique) |
| Chat history | `chat_history` | `session_id` |
| Scheme matches | `user_scheme_matches` | `(user_id, scheme_id)` unique |

Profile saves are enqueued to pgmq for async processing.

---

## 8. API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Full LangGraph pipeline |
| `GET` | `/api/chat/history` | Get chat history |
| `GET` | `/api/schemes/recommended` | DB-side eligibility scoring |
| `GET` | `/api/schemes` | List/filter schemes |
| `GET` | `/api/schemes/:id` | Scheme detail + FAQs |
| `POST` | `/api/schemes/compare` | Compare schemes |
| `POST` | `/api/schemes/simulate` | What-if simulation |
| `POST` | `/api/schemes/search` | Hybrid search |
| `GET/POST/PUT` | `/api/profile` | Profile CRUD |
| `POST` | `/api/document-upload` | Document intelligence |
| `POST` | `/api/feedback` | User feedback |
| `GET` | `/api/health` | Health check |

---

## 9. Security Considerations

| Area | Status | Notes |
|---|---|---|
| **SQL Injection** | ✅ Safe | All queries use parameterized binds (SQLAlchemy ORM + `text()` with bound params) |
| **XSS** | ✅ Safe | React JSX auto-escapes; no `dangerouslySetInnerHTML` used |
| **Auth** | ⚠️ Weak | JWT decoded without signature verification (demo system) |
| **CORS** | ✅ Safe | Not applicable (no secrets in code) |
| **Rate limiting** | ❌ Not implemented | No rate limiting on endpoints |

---

## 10. Configuration

All settings in `app/config.py` (loaded from environment):

| Setting | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `LOCAL_LLM_URL` | — | OpenAI-compatible LLM endpoint |
| `LOCAL_LLM_MODEL` | `qwen2.5:3b` | Model name for API calls |
| `EMBEDDING_MODEL` | `thenlper/gte-small` | Sentence transformer model |
| `EMBEDDING_DIM` | `384` | Vector dimension |
| `VECTOR_SEARCH_LIMIT` | `20` | Max vector results |
| `VECTOR_SEARCH_THRESHOLD` | `0.55` | Min cosine similarity |
| `HYBRID_VEC_WEIGHT` | `0.5` | Hybrid search vector weight |
| `HYBRID_TRIGRAM_WEIGHT` | `0.3` | Hybrid search trigram weight |
| `HYBRID_TEXT_WEIGHT` | `0.2` | Hybrid search full-text weight |
| `MMR_LAMBDA` | `0.5` | MMR relevance-diversity balance |
| `RETRIEVAL_VEC_SEARCH_LIMIT` | `20` | Pipeline vector search limit |
| `RETRIEVAL_MAX_CHUNKS_PER_SCHEME` | `6` | MMR max chunks per scheme |
| `RELEVANCE_THRESHOLD` | `0.3` | Min relevance to avoid retry |
| `MAX_RETRIES` | `2` | Max retrieval retries |
| `LLM_TIMEOUT` | `30` | LLM API timeout (seconds) |
| `PGVECTOR_PROBES` | `20` | IVFFlat probes for search quality |
| `EDUCATION_SEM_THRESHOLD` | `0.55` | Education embedding match threshold |

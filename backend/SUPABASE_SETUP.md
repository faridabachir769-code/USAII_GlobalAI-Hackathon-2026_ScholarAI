# ScholarAI — Supabase Setup Guide

## Overview

ScholarAI uses **Supabase** (PostgreSQL + pgvector) for:
- **Database**: Schemes, rules, embeddings, chat history, profiles
- **Vector search**: pgvector (384-dim embeddings) for semantic scheme matching
- **Auth** (optional): User authentication via Supabase Auth

---

## 1. Local Development

### 1.1 Start Local Supabase

```bash
cd backend
npx supabase start
```

This starts local services:
| Service | URL |
|---|---|
| Database (PostgreSQL) | `postgresql://postgres:postgres@localhost:54322/postgres` |
| API (Kong) | `http://127.0.0.1:54321` |
| Studio (Dashboard) | `http://127.0.0.1:54323` |
| Inbucket (Email) | `http://127.0.0.1:54324` |

### 1.2 Apply Migrations

```bash
npx supabase db push
```

### 1.3 Seed Data

Schemes are ingested via the Python pipeline (`scripts/embed_schemes.py`), not SQL seed files.

### 1.4 Stop Local Supabase

```bash
npx supabase stop
```

---

## 2. Cloud Setup

### 2.1 Create/Link a Project

```bash
# Login to Supabase
npx supabase login

# Link an existing project
npx supabase link --project-ref <project-ref-id>
```

### 2.2 Push Schema to Cloud

```bash
# Set your database password (get from Dashboard → Project Settings → Database)
$env:SUPABASE_DB_PASSWORD = "your-password"

# Push migrations
npx supabase db push
```

### 2.3 Migrate Data from Local to Cloud

Dump local data:

```bash
npx supabase db dump --local --data-only --file local_data_dump.sql
```

Restore to cloud:

```bash
$env:PGPASSWORD = "your-password"
psql -h db.<project-ref>.supabase.co -p 5432 -d postgres -U postgres -f local_data_dump.sql
```

---

## 3. Environment Configuration

### 3.1 Backend (`backend/.env`)

| Variable | Local Value | Cloud Value |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:54322/postgres` | `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres` |
| `SUPABASE_URL` | `http://127.0.0.1:54321` | `https://<ref>.supabase.co` |
| `SUPABASE_KEY` | `sb_publishable_...` | Your anon public key (Dashboard → Settings → API) |

### 3.2 Frontend (`frontend/.env`)

| Variable | Local Value | Cloud Value |
|---|---|---|
| `VITE_SUPABASE_URL` | `http://127.0.0.1:54321` | `https://<ref>.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | `sb_publishable_...` | Same anon public key as backend |

### 3.3 Getting Cloud Credentials

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Project Settings → API**
4. Copy:
   - **Project URL** → `SUPABASE_URL` / `VITE_SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY` / `VITE_SUPABASE_ANON_KEY`
5. Navigate to **Project Settings → Database**
6. Copy **Database password** (set during project creation) → for `DATABASE_URL`

---

## 4. Project Details

| Detail | Value |
|---|---|
| Project Name | ScholarAI |
| Project Ref | `nesgszpppvincbujlcrl` |
| Region | Central EU (Frankfurt) |
| Database | PostgreSQL 17 with pgvector |
| API URL | `https://nesgszpppvincbujlcrl.supabase.co` |
| Direct DB Host | `db.nesgszpppvincbujlcrl.supabase.co` |
| Pooler Host | `aws-1-eu-central-1.pooler.supabase.com` |

---

## 5. Schema Overview

| Table | Purpose |
|---|---|
| `schemes` | Scheme master data (name, benefits, eligibility, ministry, state) |
| `rules` | Eligibility rules (income, category, state, gender, education) |
| `faq` | Scheme-specific FAQs |
| `scheme_embeddings` | Vector embeddings (384-dim) for semantic search |
| `profiles` | User demographic profiles |
| `chat_history` | Conversation history |
| `llm_jobs` | Async LLM job queue |
| `search_log` | Search analytics |
| `feedback` | User feedback on recommendations |
| `user_scheme_matches` | Cached match results |
| `pgmq.*` | Message queues for async jobs |

---

## 6. Useful Commands

```bash
# View linked project
npx supabase projects list

# Dump cloud database
npx supabase db dump --data-only --file cloud_dump.sql

# Reset local database
npx supabase db reset

# View database status
npx supabase status
```

---

## 7. Troubleshooting

### "unexpected login role status 403"

Ensure the project is linked:
```bash
npx supabase link --project-ref <ref>
```

Make sure `SUPABASE_DB_PASSWORD` is set correctly.

### "relation does not exist"

Migrations assume core tables exist. Run `npx supabase db push` first, or manually create tables via SQLAlchemy's `init_db()`.

### Password with special characters

URL-encode special characters in the `DATABASE_URL`:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`

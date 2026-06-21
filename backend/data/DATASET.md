# ScholarAI Government Schemes Dataset

## Overview

This dataset contains **1,007 government schemes** scraped from [myscheme.gov.in](https://www.myscheme.gov.in), the Indian government's official scholarship and scheme portal. Each scheme is stored as an individual JSON file with structured metadata, eligibility rules, benefits, application process, and FAQs.

The dataset powers ScholarAI's RAG (Retrieval-Augmented Generation) pipeline — enabling semantic search, eligibility filtering, and personalized scheme recommendations.

## Statistics

| Metric | Value |
|---|---|
| Total schemes | 1,007 |
| Total chunks (embedded) | 14,805 |
| Total data size | ~11 MB |
| File format | JSON (one file per scheme) |
| Scrape version | 2.0.0 |
| Scrape date | 2026-06-20 |

## Coverage

### Central Schemes (224)
Schemes run by Government of India ministries applicable nationwide:

| Ministry | Count |
|---|---|
| Ministry of Education | 63 |
| Ministry of Social Justice and Empowerment | 37 |
| Ministry of Science and Technology | 28 |
| Ministry of Agriculture and Farmers Welfare | 12 |
| Ministry of Electronics and Information Technology | 8 |
| Ministry of Commerce and Industry | 7 |
| Ministry of Health and Family Welfare | 6 |
| Ministry of Minority Affairs | 5 |
| Ministry of Tribal Affairs | 5 |
| Ministry of Finance | 4 |
| Ministry of Defence | 4 |
| Ministry of Home Affairs | 4 |
| Ministry of New and Renewable Energy | 4 |
| Ministry of Labour and Employment | 3 |
| Ministry of External Affairs | 3 |
| Ministry of Communication | 3 |
| Ministry of Law and Justice | 2 |
| Ministry of Culture | 2 |
| Ministry of Textiles | 2 |
| Ministry of Statistics and Programme Implementation | 2 |
| Ministry of Ports, Shipping and Waterways | 2 |
| Ministry of Chemicals and Fertilizers | 2 |
| Ministry of Railways | 1 |
| Ministry of Panchayati Raj | 1 |
| Ministry of Jal Shakti | 1 |
| Ministry of Skill Development and Entrepreneurship | 1 |
| Ministry of Corporate Affairs | 1 |
| Ministry of Development of North Eastern Region | 1 |
| Ministry of Earth Sciences | 1 |
| Ministry of Environment, Forests and Climate Change | 2 |
| Ministry of Personnel, Public Grievances and Pensions | 2 |
| Other Central Bodies (NITI Aayog, CAG, Lokpal) | 4 |

### State-Specific Schemes (783)
Schemes administered by individual state governments, covering all 28 states and 8 union territories:

| State / UT | Count |
|---|---|
| Gujarat | 98 |
| Uttarakhand | 97 |
| Madhya Pradesh | 87 |
| Rajasthan | 55 |
| Goa | 38 |
| Puducherry | 35 |
| Tamil Nadu | 33 |
| Kerala | 30 |
| Haryana | 30 |
| Maharashtra | 27 |
| Chhattisgarh | 26 |
| Assam | 23 |
| Bihar | 19 |
| Odisha | 16 |
| Delhi | 15 |
| Himachal Pradesh | 15 |
| Andhra Pradesh | 14 |
| Dadra and Nagar Haveli and Daman and Diu | 14 |
| Uttar Pradesh | 13 |
| Jharkhand | 13 |
| Meghalaya | 12 |
| Nagaland | 11 |
| Mizoram | 10 |
| West Bengal | 7 |
| Jammu and Kashmir | 7 |
| Tripura | 6 |
| Arunachal Pradesh | 5 |
| Karnataka | 5 |
| Manipur | 5 |
| Punjab | 5 |
| Sikkim | 4 |
| Andaman and Nicobar Islands | 4 |
| Telangana | 2 |
| Chandigarh | 1 |
| Lakshadweep | 1 |

## File Format

Each scheme file follows this structure:

```json
{
  "metadata": {
    "scheme_name": "Scheme Display Name",
    "slug": "scheme-url-slug",
    "url": "https://www.myscheme.gov.in/schemes/{slug}",
    "state": "State Name or Ministry Name",
    "scraped_at": "ISO-8601 timestamp",
    "chunk_count": 16,
    "version": "2.0.0"
  },
  "raw_data": {
    "details": "Full scheme description and implementation details",
    "benefits": "Monetary and non-monetary benefits",
    "eligibility": "Eligibility criteria (age, income, category, state, etc.)",
    "exclusions": "Who is NOT eligible",
    "application_process": "Step-by-step application instructions",
    "documents_required": "Required documents list",
    "scheme_name": "Duplicate of scheme_name (for search indexing)",
    "url": "Original source URL",
    "sources_and_references": "Source links and disclaimers",
    "faqs": [
      {
        "question": "Common question",
        "answer": "Detailed answer"
      }
    ]
  }
}
```

### Key Fields

| Field | Description |
|---|---|
| `metadata.scheme_name` | Display name of the scheme |
| `metadata.state` | Governing body — either an Indian state name (state-specific) or Ministry name (central scheme) |
| `metadata.chunk_count` | Number of text chunks generated for embedding |
| `raw_data.details` | Full scheme description and implementation context |
| `raw_data.benefits` | Detailed benefits including monetary amounts (₹) |
| `raw_data.eligibility` | Eligibility rules (age, income, category, state residency, etc.) |
| `raw_data.application_process` | Step-by-step application procedure |
| `raw_data.documents_required` | List of documents needed |
| `raw_data.faqs` | Frequently asked questions with answers |

## Supporting File

### `discovered_schemes.json`

A flat mapping of all scraped scheme slugs to their display names:

```json
{
  "aabym": "Aam Aadmi Bima Yojana (Maharashtra)",
  "rgisfm": "Research Grant For In-Service Faculty Members",
  ...
}
```

**Size:** 77 KB  
**Purpose:** Quick lookup from slug → scheme name without loading individual files.

## Usage

### Python

```python
import json
from pathlib import Path

DATA_DIR = Path("backend/data/scraped_schemes")

# Load all schemes
schemes = []
for f in sorted(DATA_DIR.glob("*_rag.json")):
    with open(f) as fh:
        schemes.append(json.load(fh))

# Filter by state
gujarat_schemes = [s for s in schemes if s["metadata"]["state"] == "Gujarat"]

# Filter central schemes (by ministry name)
central = [s for s in schemes if s["metadata"]["state"].startswith("Ministry")]
```

### Seeding to Database

The dataset is processed by `backend/app/text_preprocessor.py` which:
1. Reads each JSON file
2. Chunks the raw text into overlapping segments (max 450 tokens, 60-token overlap)
3. Generates embeddings via SentenceTransformer (`all-MiniLM-L6-v2`, 384-dim)
4. Stores chunks and embeddings in the `scheme_embeddings` table in Supabase/PostgreSQL

## License

This dataset is collected from publicly available information on [myscheme.gov.in](https://www.myscheme.gov.in), the Indian government's open portal for citizen-centric schemes. All scheme data belongs to the respective government departments. This dataset is provided for educational and research purposes.

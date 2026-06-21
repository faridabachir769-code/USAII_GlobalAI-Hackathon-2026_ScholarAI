# Scraped Schemes Summary

## Total: 1007 schemes (out of 1010 discovered)

## Classification

Schemes are classified by **jurisdiction** stored in `metadata.state`:

- **Central / All India**: 224 schemes — tagged with ministry names (e.g., "Ministry of Education", "Ministry of Social Justice and Empowerment"). Available nationwide.
- **State / UT**: 783 schemes — tagged with state or UT name (e.g., "Gujarat", "Delhi"). Only applicable within that state.

## Data Format

Each scheme is stored as `{slug}_rag.json` with:

```json
{
  "metadata": {
    "scheme_name": "...",
    "slug": "...",
    "url": "https://www.myscheme.gov.in/schemes/{slug}",
    "state": "Gujarat" | "Ministry of Education" | etc.,
    "scraped_at": "ISO timestamp",
    "chunk_count": N
  },
  "raw_data": {
    "scheme_name", "slug", "url", "state",
    "details", "benefits", "eligibility", "exclusions",
    "application_process", "documents_required",
    "sources_and_references",
    "faqs": [{"question": "...", "answer": "..."}, ...]
  },
  "rag_chunks": [
    {"content": "...", "metadata": {"section": "details|benefits|...", "scheme": "...", "state": "..."}},
    ...
  ]
}
```

## Source

All schemes scraped from https://www.myscheme.gov.in (Education & Learning category).

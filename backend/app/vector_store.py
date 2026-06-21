import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
if os.getenv("HF_TOKEN"):
    os.environ.setdefault("HUGGINGFACEHUB_API_TOKEN", os.environ["HF_TOKEN"])

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings

logger = logging.getLogger(__name__)

# ── Embedding model (lazy init) ───────────────────────────────────────────────

_device = None
def _get_device():
    global _device
    if _device is None:
        import torch
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    return _device

_sentence_model = None

def _get_embedder():
    global _sentence_model
    if _sentence_model is None:
        from sentence_transformers import SentenceTransformer
        model_name = settings.EMBEDDING_MODEL
        dev = _get_device()
        logger.info(f"Loading sentence-transformers model: {model_name} on {dev}")
        _sentence_model = SentenceTransformer(model_name, device=dev)
    return _sentence_model

EMBEDDING_DIM = settings.EMBEDDING_DIM


def get_embedding(text: str, is_query: bool = False) -> List[float]:
    processed_text = text
    if settings.EMBEDDING_MODEL.startswith("Supabase/gte") or "gte" in settings.EMBEDDING_MODEL.lower():
        prefix = "query: " if is_query else "passage: "
        if not text.startswith("query: ") and not text.startswith("passage: "):
            processed_text = prefix + text

    model = _get_embedder()
    emb = model.encode(processed_text, normalize_embeddings=True)
    return emb.tolist()


def get_embeddings_batch(texts: List[str], is_query: bool = False) -> List[List[float]]:
    if not texts:
        return []

    processed_texts = []
    for text in texts:
        processed_text = text
        if settings.EMBEDDING_MODEL.startswith("Supabase/gte") or "gte" in settings.EMBEDDING_MODEL.lower():
            prefix = "query: " if is_query else "passage: "
            if not text.startswith("query: ") and not text.startswith("passage: "):
                processed_text = prefix + text
        processed_texts.append(processed_text)

    model = _get_embedder()
    embs = model.encode(processed_texts, normalize_embeddings=True, show_progress_bar=False)
    return embs.tolist()


# ── pgvector search (PostgreSQL only) ────────────────────────────────────────

IS_POSTGRES = settings.DATABASE_URL.startswith("postgresql") or "supabase" in settings.DATABASE_URL

PGVECTOR_PROBES = settings.PGVECTOR_PROBES
VECTOR_SEARCH_THRESHOLD = settings.VECTOR_SEARCH_THRESHOLD
VECTOR_SEARCH_LIMIT = settings.VECTOR_SEARCH_LIMIT

HYBRID_VEC_W = settings.HYBRID_VEC_WEIGHT
HYBRID_TRIGRAM_W = settings.HYBRID_TRIGRAM_WEIGHT
HYBRID_TEXT_W = settings.HYBRID_TEXT_WEIGHT


def search_pgvector(
    db: Session,
    query: str,
    limit: int = None,
    threshold: float = None,
    scheme_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    if limit is None:
        limit = VECTOR_SEARCH_LIMIT
    if threshold is None:
        threshold = VECTOR_SEARCH_THRESHOLD

    if not IS_POSTGRES:
        raise RuntimeError(
            "pgvector search requires PostgreSQL. "
            "Set DATABASE_URL to a PostgreSQL/Supabase URL."
        )

    query_vec = get_embedding(query, is_query=True)

    if scheme_ids:
        sql = text("""
            SELECT
                se.id,
                se.scheme_id,
                se.chunk_index,
                se.section,
                se.content,
                1 - (se.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM scheme_embeddings se
            WHERE 1 - (se.embedding <=> CAST(:query_vec AS vector)) > :threshold
              AND se.scheme_id IN :scheme_ids
            ORDER BY se.embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit
        """)
        params = {
            "query_vec": json.dumps(query_vec),
            "threshold": threshold,
            "limit": limit,
            "scheme_ids": tuple(scheme_ids)
        }
    else:
        sql = text("""
            SELECT
                se.id,
                se.scheme_id,
                se.chunk_index,
                se.section,
                se.content,
                1 - (se.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM scheme_embeddings se
            WHERE 1 - (se.embedding <=> CAST(:query_vec AS vector)) > :threshold
            ORDER BY se.embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit
        """)
        params = {
            "query_vec": json.dumps(query_vec),
            "threshold": threshold,
            "limit": limit
        }

    try:
        db.execute(text(f"SET ivfflat.probes = {PGVECTOR_PROBES}"))
        rows = db.execute(sql, params).fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row.id,
                "scheme_id": row.scheme_id,
                "chunk_index": row.chunk_index,
                "section": row.section,
                "text": row.content,
                "score": float(row.similarity),
                "relevance_score": float(row.similarity),
                "payload": {
                    "scheme_id": row.scheme_id,
                    "section": row.section,
                }
            })

        return results[:limit]
    except Exception as e:
        logger.error(f"pgvector search failed: {e}")
        raise


def search_hybrid(
    db: Session,
    query: str,
    limit: int = 20,
    min_score: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Hybrid search using PostgreSQL function:
    vector cosine similarity + pg_trgm fuzzy match + tsvector full-text.
    """
    if not IS_POSTGRES:
        return search_pgvector(db, query, limit, threshold=min_score)

    query_vec = get_embedding(query, is_query=True)
    query_vec_json = json.dumps(query_vec)

    sql = text("""
        SELECT * FROM search_schemes_hybrid(
            search_query    := :q,
            query_embedding := CAST(:vec AS vector),
            max_results     := :lim,
            min_score       := :min_sc
        )
    """)

    try:
        rows = db.execute(sql, {
            "q": query,
            "vec": query_vec_json,
            "lim": limit,
            "min_sc": min_score
        }).fetchall()

        results = []
        for row in rows:
            results.append({
                "scheme_id": row.scheme_id,
                "scheme_name": row.scheme_name,
                "score": float(row.combined_score),
                "relevance_score": float(row.combined_score),
                "vector_score": float(row.similarity),
                "trigram_score": float(row.trigram_score),
                "text_score": float(row.text_score),
                "section": row.section,
                "text": row.content_snippet,
                "payload": {
                    "scheme_id": row.scheme_id,
                    "section": row.section,
                }
            })

        logger.info(
            f"Hybrid search: '{query[:40]}...' "
            f"→ {len(results)} results "
            f"(vec={HYBRID_VEC_W}, trigram={HYBRID_TRIGRAM_W}, text={HYBRID_TEXT_W})"
        )
        return results
    except Exception as e:
        logger.warning(f"Hybrid search failed, falling back to vector-only: {e}")
        return search_pgvector(db, query, limit, threshold=min_score)


# ── Unified public API ────────────────────────────────────────────────────────

def upsert_document(doc_id: int, text: str, payload: Dict[str, Any]):
    from app.database import SessionLocal, SchemeEmbedding

    embedding = get_embedding(text, is_query=False)

    if not IS_POSTGRES:
        raise RuntimeError("upsert_document requires PostgreSQL with pgvector.")

    db: Session = SessionLocal()
    try:
        existing = db.query(SchemeEmbedding).filter(SchemeEmbedding.id == doc_id).first()
        if existing:
            existing.content = text
            existing.embedding = embedding
            existing.section = payload.get("section", existing.section)
        else:
            db.add(SchemeEmbedding(
                id=doc_id,
                scheme_id=payload.get("scheme_id", 0),
                chunk_index=payload.get("chunk_index", 0),
                section=payload.get("section", ""),
                content=text,
                embedding=embedding,
            ))
        db.commit()
    except Exception as e:
        logger.error(f"pgvector upsert failed: {e}")
        raise
    finally:
        db.close()


def search_similar_documents(
    query: str,
    db: Optional[Session] = None,
    limit: int = None,
    threshold: float = None,
    scheme_ids: Optional[List[int]] = None,
    use_hybrid: bool = True,
) -> List[Dict[str, Any]]:
    if limit is None:
        limit = VECTOR_SEARCH_LIMIT
    if threshold is None:
        threshold = VECTOR_SEARCH_THRESHOLD

    if not IS_POSTGRES:
        raise RuntimeError(
            "pgvector search requires PostgreSQL. "
            "Set DATABASE_URL to a PostgreSQL/Supabase URL."
        )

    def _search(_db):
        if use_hybrid and not scheme_ids:
            return search_hybrid(_db, query, limit=limit * 2, min_score=threshold)
        return search_pgvector(_db, query, limit, threshold, scheme_ids)

    if db is not None:
        return _search(db)

    from app.database import SessionLocal
    _db = SessionLocal()
    try:
        return _search(_db)
    finally:
        _db.close()

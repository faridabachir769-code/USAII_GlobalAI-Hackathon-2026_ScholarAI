import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "docker.io/ai/qwen2.5:3B-Q4_K_M")
    LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "30.0"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./scholarai.db")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Vector search
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "384"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "thenlper/gte-small")
    VECTOR_SEARCH_THRESHOLD: float = float(os.getenv("VECTOR_SEARCH_THRESHOLD", "0.55"))
    VECTOR_SEARCH_LIMIT: int = int(os.getenv("VECTOR_SEARCH_LIMIT", "15"))
    PGVECTOR_PROBES: int = int(os.getenv("PGVECTOR_PROBES", "10"))

    # Hybrid search weights (vector + trigram + full-text)
    HYBRID_VEC_WEIGHT: float = float(os.getenv("HYBRID_VEC_WEIGHT", "0.5"))
    HYBRID_TRIGRAM_WEIGHT: float = float(os.getenv("HYBRID_TRIGRAM_WEIGHT", "0.3"))
    HYBRID_TEXT_WEIGHT: float = float(os.getenv("HYBRID_TEXT_WEIGHT", "0.2"))

    # Chunking
    CHUNK_MAX_TOKENS: int = int(os.getenv("CHUNK_MAX_TOKENS", "450"))
    CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "60"))

    # Retrieval agent
    RETRIEVAL_VEC_SEARCH_LIMIT: int = int(os.getenv("RETRIEVAL_VEC_SEARCH_LIMIT", "50"))
    RETRIEVAL_MAX_CHUNKS_PER_SCHEME: int = int(os.getenv("RETRIEVAL_MAX_CHUNKS_PER_SCHEME", "6"))
    MMR_LAMBDA: float = float(os.getenv("MMR_LAMBDA", "0.5"))

    # Relevance verifier
    RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "0.50"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))

    # Cache / Queue
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    PGMQ_ENABLED: bool = os.getenv("PGMQ_ENABLED", "true").lower() == "true"

    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

settings = Settings()

if settings.HF_TOKEN:
    os.environ["HF_TOKEN"] = settings.HF_TOKEN
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = settings.HF_TOKEN

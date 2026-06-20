from typing import List, Tuple

from app.core.config import settings
from app.core.logger import get_logger
from app.db.models import Scheme
from sqlalchemy import text
from sqlalchemy.orm import Session

log = get_logger(__name__)


class VectorSearchService:
    """
    Service for performing vector similarity search on schemes.
    Assumes pgvector extension is enabled in PostgreSQL.
    """

    def __init__(self):
        self.top_k = settings.vector_search_top_k

    async def search_similar_schemes(
        self, db: Session, embedding: List[float]
    ) -> List[Tuple[Scheme, float]]:
        """
        Searches for similar schemes in the database using vector similarity.
        Returns a list of (Scheme, similarity_score) tuples.
        """
        if not embedding:
            return []

        try:
            # Convert the embedding list to a PostgreSQL vector literal
            embedding_str = f"[{','.join(map(str, embedding))}]"

            # Use raw SQL via text() for the pgvector <-> (cosine distance) operator.
            # The embedding column is stored as JSON, so we cast it to vector.
            results = (
                db.query(
                    Scheme,
                    text(f"embedding::vector <-> '{embedding_str}'::vector").label(
                        "similarity"
                    ),
                )
                .order_by(text("similarity"))
                .limit(self.top_k)
                .all()
            )

            # pgvector returns distance, so similarity = 1 - distance.
            return [(scheme, 1 - distance) for scheme, distance in results]

        except Exception as e:
            log.error(f"Error during vector search: {e}")
            return []

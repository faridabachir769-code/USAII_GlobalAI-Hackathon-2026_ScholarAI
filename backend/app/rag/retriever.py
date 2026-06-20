from typing import List, Tuple

from pydantic import UUID4
from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..db.models import Profile, Scheme
from .embedding import EmbeddingService
from .vector_search import VectorSearchService

log = get_logger(__name__)


class Retriever:
    """
    Orchestrates the retrieval of relevant schemes based on a user profile and query.
    It uses embedding generation and vector search to find similar schemes.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_search_service = VectorSearchService()

    async def retrieve_schemes(
        self, db: Session, profile_id: UUID4
    ) -> List[Tuple[Scheme, float]]:
        """
        Retrieves a list of schemes relevant to the given profile.

        1. Fetches the user profile.
        2. Creates an embedding for the profile (based on its attributes).
        3. Performs a vector search to find schemes with similar embeddings.
        4. Returns the schemes along with their similarity scores.
        """
        log.info(f"Retrieving schemes for profile_id: {profile_id}")

        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            log.warning(f"Profile not found: {profile_id}")
            return []

        # Create an embedding for the profile's characteristics
        profile_text = (
            f"User profile for {profile.name}. "
            f"Age: {profile.age}, State: {profile.state}, Income: {profile.income}. "
            f"Occupation: {profile.occupation}, Education: {profile.education_level}. "
            f"Category: {profile.category}, Goals: {profile.goals}."
        )
        profile_embedding = await self.embedding_service.create_embedding(profile_text)

        if not profile_embedding:
            log.error(f"Failed to create embedding for profile {profile_id}")
            return []

        # Perform vector search to find similar schemes
        similar_schemes = await self.vector_search_service.search_similar_schemes(
            db, profile_embedding
        )

        log.info(
            f"Found {len(similar_schemes)} similar schemes for profile {profile_id}"
        )
        return similar_schemes

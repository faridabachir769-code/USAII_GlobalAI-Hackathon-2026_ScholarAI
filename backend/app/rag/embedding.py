from typing import List

import openai

from ..core.config import settings
from ..core.logger import get_logger
from ..db.models import Scheme

log = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating and managing vector embeddings for schemes.
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.openai_embedding_model
        self.embedding_dimensions = settings.openai_embedding_dimensions

    async def create_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the given text using OpenAI.
        """
        if not text:
            return []

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model,
                dimensions=self.embedding_dimensions,
            )
            return response.data[0].embedding
        except Exception as e:
            log.error(f"Error creating embedding: {e}")
            return []

    async def embed_scheme(self, scheme: Scheme) -> List[float]:
        """
        Generates a combined embedding for a scheme from its name, description, benefits, and eligibility.
        """
        combined_text = (
            f"{scheme.scheme_name}. "
            f"{scheme.description}. "
            f"Benefits: {scheme.benefits}. "
            f"Eligibility: {scheme.eligibility}."
        )
        return await self.create_embedding(combined_text)

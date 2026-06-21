from typing import Any, Dict, List

import openai

from ..core.config import settings
from ..core.logger import get_logger

log = get_logger(__name__)


class LLMService:
    """
    Service for interacting with OpenAI GPT models for text analysis and generation.
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def call_gpt(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generic method to call OpenAI GPT.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            return content if content is not None else "No response generated."
        except Exception as e:
            log.error(f"Error calling GPT: {e}")
            return "Error: Unable to generate response from AI service."

    async def analyze_schemes(
        self, profile_data: Dict[str, Any], schemes: List[Dict[str, Any]]
    ) -> str:
        """
        Uses GPT to analyze and compare schemes based on a user profile.
        """
        system_prompt = "You are an expert government scheme advisor. Compare the following schemes for the user based on their profile."
        user_prompt = f"User Profile: {profile_data}\n\nSchemes to compare: {schemes}"

        return await self.call_gpt(system_prompt, user_prompt)

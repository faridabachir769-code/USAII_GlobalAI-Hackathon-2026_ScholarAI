from typing import Any, Dict, List

from ..core.logger import get_logger
from ..db.models import Profile, Scheme
from .llm_service import LLMService

log = get_logger(__name__)


class ComparisonAnalyzer:
    """
    Analyzer for comparing multiple schemes using LLM.
    """

    def __init__(self):
        self.llm_service = LLMService()

    async def compare_schemes(
        self, profile: Profile, schemes: List[Scheme]
    ) -> Dict[str, Any]:
        """
        Performs a detailed comparison of multiple schemes for a user profile.
        """
        profile_data = {
            "name": profile.name,
            "age": profile.age,
            "state": profile.state,
            "income": profile.income,
            "occupation": profile.occupation,
            "education": profile.education_level,
            "category": profile.category,
            "goals": profile.goals,
        }

        schemes_data = [
            {
                "name": s.scheme_name,
                "category": s.category,
                "description": s.description,
                "benefits": s.benefits,
                "eligibility": s.eligibility,
            }
            for s in schemes
        ]

        analysis_text = await self.llm_service.analyze_schemes(
            profile_data, schemes_data
        )

        # In a more advanced implementation, we could ask GPT to return JSON
        # and parse it into structured benefits, drawbacks, etc.
        # For now, we return the text and some metadata.

        return {
            "comparison_text": analysis_text,
            "schemes_compared": [s.scheme_name for s in schemes],
        }

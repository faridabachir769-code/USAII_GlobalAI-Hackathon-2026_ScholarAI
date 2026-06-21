from typing import Any, Dict, List

from ..core.config import settings
from ..core.logger import get_logger
from ..db.models import Profile, Scheme

log = get_logger(__name__)


class DecisionEngine:
    """
    Engine for scoring and ranking government schemes based on user profile.
    """

    def __init__(self):
        # Load weights from config (see Settings.decision_engine_weights)
        weights = settings.decision_engine_weights
        self.w_eligibility = weights.get("eligibility", 0.40)
        self.w_benefit = weights.get("benefit", 0.25)
        self.w_goal = weights.get("goal_alignment", 0.25)
        self.w_complexity = weights.get("complexity", 0.10)

    def score_scheme(self, profile: Profile, scheme: Scheme) -> Dict[str, Any]:
        """
        Calculates a score for a single scheme based on multiple criteria.
        Returns a breakdown of scores.
        """
        # Logic to calculate sub-scores (simplified for now)
        # In a real scenario, these would involve more complex rule-matching or LLM-based scoring

        # 1. Eligibility Score (0-100)
        # Check if state matches, income is within range, etc.
        eligibility_score = 100.0 if profile.state in scheme.state else 50.0

        # 2. Benefit Score (0-100)
        # Higher score for schemes with more benefits or higher grant amounts
        benefit_score = 80.0  # Placeholder

        # 3. Goal Alignment (0-100)
        # Check if scheme category matches user goals
        goal_score = 90.0 if scheme.category.lower() in profile.goals.lower() else 40.0

        # 4. Complexity Score (0-100)
        # Inverse of number of application steps or documents
        complexity_score = max(0, 100 - (len(scheme.application_steps or []) * 10))

        total_score = (
            (eligibility_score * self.w_eligibility)
            + (benefit_score * self.w_benefit)
            + (goal_score * self.w_goal)
            + (complexity_score * self.w_complexity)
        )

        return {
            "eligibility_score": eligibility_score,
            "benefit_score": benefit_score,
            "goal_alignment_score": goal_score,
            "complexity_score": complexity_score,
            "total_score": round(total_score, 2),
        }

    def rank_schemes(
        self, profile: Profile, schemes: List[Scheme]
    ) -> List[Dict[str, Any]]:
        """
        Scores and ranks a list of schemes.
        """
        scored_schemes = []
        for scheme in schemes:
            score_data = self.score_scheme(profile, scheme)
            scored_schemes.append(
                {
                    "scheme": scheme,
                    "score_breakdown": score_data,
                    "total_score": score_data["total_score"],
                }
            )

        # Sort by total score descending
        return sorted(scored_schemes, key=lambda x: x["total_score"], reverse=True)

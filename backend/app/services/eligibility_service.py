"""
ELIGIBILITY SERVICE - Business Logic for Scheme Eligibility
===========================================================

This service encapsulates the logic for determining scheme eligibility for a user profile.
It combines rule-based filtering with (eventually) vector search-based relevance.
"""

from typing import List, Tuple

from app.api.schemas import EligibleSchemeResult
from app.core.logger import get_logger
from app.db.models import Profile, Scheme

log = get_logger(__name__)


class EligibilityService:
    def __init__(self):
        pass

    def filter_eligible_schemes(
        self,
        profile: Profile,
        schemes_with_scores: List[Tuple[Scheme, float]],
    ) -> List[EligibleSchemeResult]:
        """
        Filters a list of schemes based on a user's profile using rule-based logic.

        This method applies deterministic rules (e.g., state, income, age) to determine
        initial eligibility. It will later be augmented by vector search.

        Args:
            profile: The user's profile object.
            schemes_with_scores: A list of (Scheme, match_score) tuples.

        Returns:
            A list of EligibleSchemeResult objects for schemes the user is eligible for.
        """
        eligible_results: List[EligibleSchemeResult] = []

        for scheme, match_score in schemes_with_scores:
            is_eligible, reasons = self._check_scheme_rules(profile, scheme)

            if is_eligible:
                eligible_results.append(
                    EligibleSchemeResult(
                        id=str(scheme.id),
                        scheme_name=scheme.scheme_name,
                        category=scheme.category,
                        match_score=match_score,
                        eligibility_reason=". ".join(reasons),
                    )
                )
        log.info(
            f"Found {len(eligible_results)} rule-eligible schemes for profile {profile.id}"
        )
        return eligible_results

    @staticmethod
    def _check_scheme_rules(profile: Profile, scheme: Scheme) -> Tuple[bool, List[str]]:
        """
        Applies rule-based filtering for a single scheme against a user profile.

        Returns a tuple: (is_eligible, list_of_reasons).
        """
        reasons: List[str] = []
        is_eligible = True

        # Rule 1: State matching
        scheme_states = [
            s.strip().lower() for s in scheme.state.split(",")
        ]  # Handle comma-separated states
        if profile.state.lower() not in scheme_states:
            is_eligible = False
            reasons.append(f"Not available in your state ({profile.state}).")
        else:
            reasons.append(f"Available in your state ({profile.state}).")

        # Rule 2: Income eligibility (placeholder - would involve parsing scheme.eligibility)
        # For now, assume a scheme is income-eligible if profile income is positive
        # A real implementation would parse scheme.eligibility for income upper/lower bounds.
        if (
            profile.income <= 0
        ):  # Example placeholder: assuming scheme requires positive income
            is_eligible = False
            reasons.append("Income must be positive for this scheme.")
        else:
            reasons.append("Your income meets basic requirements.")

        # Rule 3: Age eligibility (placeholder - would involve parsing scheme.eligibility)
        # Assume a scheme requires an age between 18 and 60 for simplicity
        if not (18 <= profile.age <= 60):
            is_eligible = False
            reasons.append(
                "Your age is outside the typical range for this scheme (18-60)."
            )
        else:
            reasons.append("Your age is within typical eligibility.")

        # Rule 4: Category / Occupation / Education (placeholder)
        # Further parsing of scheme.eligibility string would be needed here
        # For example, if scheme.eligibility contains "students only" and profile.occupation != "student"
        if scheme.category.lower() == profile.category.lower():
            reasons.append(f"Matches your profile category ({profile.category}).")
        else:
            reasons.append(
                f"Scheme category ({scheme.category}) might not directly align with your profile category ({profile.category})."
            )

        # Combine reasons to give a comprehensive explanation.
        final_reasons = [
            r for r in reasons if not r.startswith("Not available")
        ]  # Only show positive reasons if eligible
        if not is_eligible:
            final_reasons = [r for r in reasons if r.startswith("Not available")]

        return is_eligible, final_reasons if final_reasons else [
            "Meets general criteria."
        ]

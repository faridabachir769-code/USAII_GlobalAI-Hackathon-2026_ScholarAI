"""
RECOMMENDATION SERVICE - Orchestrates Scheme Comparison and Decision Reports
===========================================================================

This service coordinates the process of comparing schemes and generating decision reports.
It will integrate with the RAG and AI layers to provide intelligent recommendations.
"""

from typing import Any, Dict, List, Tuple
from uuid import UUID

from app.ai.comparison_analyzer import ComparisonAnalyzer
from app.ai.decision_engine import DecisionEngine
from app.api.schemas import (
    ComparisonAnalysis,
    RecommendedScheme,
    ScoringBreakdown,
)
from app.core.logger import get_logger
from app.db.models import Profile, Scheme, SchemeComparison
from sqlalchemy.orm import Session

log = get_logger(__name__)


class RecommendationService:
    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.comparison_analyzer = ComparisonAnalyzer()

    async def compare_schemes(
        self,
        db: Session,
        profile: Profile,
        schemes: List[Scheme],
    ) -> Tuple[ComparisonAnalysis, str]:
        """
        Compares multiple schemes for a profile using the AI analyzer.
        """
        log.info(
            f"Generating AI comparison for profile {profile.id} with schemes {[s.id for s in schemes]}"
        )

        comparison_data = await self.comparison_analyzer.compare_schemes(
            profile, schemes
        )

        # Parse the results into ComparisonAnalysis
        # For now, we'll map the combined text to the fields if we don't have structured output
        # In a real system, we'd prompt the LLM to return JSON with these exact fields.

        analysis = ComparisonAnalysis(
            benefits_summary=comparison_data.get(
                "benefits_summary", "See detailed explanation."
            ),
            drawbacks_summary=comparison_data.get(
                "drawbacks_summary", "See detailed explanation."
            ),
            application_ease=comparison_data.get(
                "application_ease", "See detailed explanation."
            ),
            processing_time=comparison_data.get(
                "processing_time", "See detailed explanation."
            ),
        )

        llm_explanation = comparison_data.get(
            "comparison_text", "AI comparison completed."
        )

        return analysis, llm_explanation

    async def generate_decision_report(
        self,
        db: Session,
        profile: Profile,
        schemes: List[Scheme],
    ) -> Tuple[RecommendedScheme, List[Dict[str, Any]], List[str], str]:
        """
        Generates a comprehensive decision report for a set of schemes using the Decision Engine.
        """
        log.info(
            f"Generating decision report for profile {profile.id} with schemes {[s.id for s in schemes]}"
        )

        ranked_results = self.decision_engine.rank_schemes(profile, schemes)

        if not ranked_results:
            raise ValueError("No schemes to rank")

        best_match = ranked_results[0]
        scheme = best_match["scheme"]
        scores = best_match["score_breakdown"]

        scoring_breakdown = ScoringBreakdown(
            eligibility_score=scores["eligibility_score"],
            benefit_score=scores["benefit_score"],
            goal_alignment_score=scores["goal_alignment_score"],
            complexity_score=scores["complexity_score"],
            total_score=scores["total_score"],
        )

        recommended = RecommendedScheme(
            id=str(scheme.id),
            scheme_name=scheme.scheme_name,
            category=scheme.category,
            score=scores["total_score"],
            scoring_breakdown=scoring_breakdown,
            reasons=[
                f"Highest alignment with your goals ({scores['goal_alignment_score']}/100)",
                f"Strong eligibility match ({scores['eligibility_score']}/100)",
            ],
            next_steps=scheme.application_steps or ["Visit official website to apply"],
        )

        all_schemes = [
            {
                "id": str(r["scheme"].id),
                "scheme_name": r["scheme"].scheme_name,
                "score": r["total_score"],
            }
            for r in ranked_results
        ]

        tradeoffs = ["Consider processing time vs grant amount for the top choices."]
        summary = f"Based on our analysis, {scheme.scheme_name} is the best fit for your current goals."

        return recommended, all_schemes, tradeoffs, summary

    @staticmethod
    def save_comparison_report(
        db: Session, profile_id: UUID, scheme_ids: List[UUID], report: Dict[str, Any]
    ) -> SchemeComparison:
        """
        Saves a generated comparison report to the database.
        """
        db_comparison = SchemeComparison(
            profile_id=profile_id,
            scheme_ids=[str(sid) for sid in scheme_ids],  # Store as list of strings
            report=report,
        )
        db.add(db_comparison)
        db.commit()
        db.refresh(db_comparison)
        log.info(f"Comparison report saved: {db_comparison.id}")
        return db_comparison

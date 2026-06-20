from typing import Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.decision_engine import DecisionEngine
from app.core.logger import get_logger
from app.db.models import Profile, Scheme
from app.rag.retriever import Retriever
from app.services.eligibility_service import EligibilityService
from app.services.recommendation_service import RecommendationService

log = get_logger(__name__)


class RecommendationPipeline:
    """
    Orchestrates the entire recommendation process, from retrieval to final report generation.
    """

    def __init__(self):
        self.retriever = Retriever()
        self.eligibility_service = EligibilityService()
        self.decision_engine = DecisionEngine()
        self.recommendation_service = RecommendationService()

    async def run(
        self, profile_id: UUID, db: Session
    ) -> Dict[str, Any]:  # Adjust return type as needed
        """
        Executes the recommendation pipeline for a given profile.
        """
        log.info(f"Starting recommendation pipeline for profile_id: {profile_id}")

        # Step 1: Retrieve relevant schemes using the RAG layer
        # The retriever returns a list of (Scheme, similarity_score) tuples
        retrieved_schemes_with_scores = await self.retriever.retrieve_schemes(
            db, profile_id
        )

        # Extract only Scheme objects for subsequent steps
        retrieved_schemes = [scheme for scheme, score in retrieved_schemes_with_scores]
        if not retrieved_schemes:
            log.warning("No schemes retrieved for profile.")
            return {"error": "No relevant schemes found"}

        # Fetch the profile object if not already passed
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            log.error(f"Profile not found for ID: {profile_id}")
            return {"error": "Profile not found"}

        # Step 2: Filter by rules (Eligibility Service)
        # Note: EligibilityService.filter_eligible_schemes expects List[Tuple[Scheme, float]]
        eligible_schemes_results = self.eligibility_service.filter_eligible_schemes(
            profile, retrieved_schemes_with_scores
        )

        # Extract Scheme objects from EligibleSchemeResult for Decision Engine and ComparisonAnalyzer
        eligible_scheme_objects = [
            db.query(Scheme).filter(Scheme.id == UUID(res.id)).first()
            for res in eligible_schemes_results
            if res.id
        ]
        # Filter out any None values if a scheme was not found (should not happen if IDs are valid)
        eligible_scheme_objects = [s for s in eligible_scheme_objects if s]

        if not eligible_scheme_objects:
            log.warning("No schemes eligible after rule-based filtering.")
            return {"message": "No schemes eligible based on current rules."}

        # Step 3: Score using Decision Engine
        self.decision_engine.rank_schemes(profile, eligible_scheme_objects)

        # Step 4: LLM analysis for comparison (uses only eligible schemes)
        # Route through RecommendationService which wraps ComparisonAnalyzer
        # and returns a proper (ComparisonAnalysis, str) tuple
        (
            comparison_analysis,
            llm_explanation,
        ) = await self.recommendation_service.compare_schemes(
            db, profile, eligible_scheme_objects
        )

        # Step 5: Generate report
        # The generate_decision_report method will use the scored schemes and comparison results
        # It returns a structured report. We need to adapt its return to match expected output.
        (
            recommended_scheme,
            all_schemes_with_scores,
            tradeoffs,
            summary,
        ) = await self.recommendation_service.generate_decision_report(
            db, profile, eligible_scheme_objects
        )

        # Construct the final report structure
        final_report = {
            "profile_id": str(profile.id),
            "recommended_scheme": recommended_scheme.model_dump(),  # Use model_dump() for Pydantic v2+
            "all_schemes": all_schemes_with_scores,
            "tradeoffs": tradeoffs,
            "summary": summary,
            "comparison_analysis": comparison_analysis.model_dump(),
            "llm_explanation": llm_explanation,
            "eligibility_results": [
                res.model_dump() for res in eligible_schemes_results
            ],
        }

        log.info("Recommendation pipeline completed successfully.")
        return final_report

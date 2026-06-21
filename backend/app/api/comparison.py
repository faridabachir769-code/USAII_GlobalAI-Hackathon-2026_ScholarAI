from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import ComparisonRequest, ComparisonResponse, SchemeResponse
from app.db.base import get_db
from app.db.models import Profile, Scheme
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post(
    "/compare",
    response_model=ComparisonResponse,
)
async def compare_schemes(request: ComparisonRequest, db: Session = Depends(get_db)):
    """
    Compares multiple government schemes based on a user profile.
    """
    try:
        profile_uuid = UUID(request.profile_id)
        scheme_uuids = [UUID(sid) for sid in request.scheme_ids]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format in profile_id or scheme_ids",
        )

    profile = db.query(Profile).filter(Profile.id == profile_uuid).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {request.profile_id} not found",
        )

    schemes = db.query(Scheme).filter(Scheme.id.in_(scheme_uuids)).all()
    if len(schemes) != len(request.scheme_ids):
        found_ids = {str(s.id) for s in schemes}
        missing_ids = set(request.scheme_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme(s) not found: {', '.join(missing_ids)}",
        )

    rec_service = RecommendationService()
    analysis, llm_explanation = await rec_service.compare_schemes(db, profile, schemes)

    # Convert Scheme ORM objects to SchemeResponse using Pydantic v2 model_validate
    # This handles type coercion (UUID→str, Text→str, JSONB→list) automatically
    schemes_response = [SchemeResponse.model_validate(s) for s in schemes]

    return ComparisonResponse(
        profile_id=str(profile.id),
        schemes_compared=schemes_response,
        analysis=analysis,
        llm_explanation=llm_explanation,
    )

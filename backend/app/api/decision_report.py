from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import DecisionReportRequest, DecisionReportResponse
from app.db.base import get_db
from app.db.models import Profile, Scheme
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post(
    "/decision-report",
    response_model=DecisionReportResponse,
)
async def generate_decision_report(
    request: DecisionReportRequest, db: Session = Depends(get_db)
):
    """
    Generates a comprehensive decision report and recommendation for schemes based on a user profile.
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
    (
        recommended_scheme,
        all_schemes,
        tradeoffs,
        summary,
    ) = await rec_service.generate_decision_report(db, profile, schemes)

    return DecisionReportResponse(
        profile_id=str(profile.id),
        recommended_scheme=recommended_scheme,
        all_schemes=all_schemes,
        tradeoffs=tradeoffs,
        summary=summary,
    )

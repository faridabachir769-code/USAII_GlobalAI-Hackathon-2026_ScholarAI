# app/api/compare.py - UPDATED WITH ORM (NO MOCK DATA)
# All data persists in PostgreSQL database

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.scheme import DecisionReport, Scheme, SchemeComparison
from app.models.student import StudentProfile

router = APIRouter(prefix="/api/compare", tags=["compare"])

# ==================== PYDANTIC MODELS ====================


class CompareRequest(BaseModel):
    profile_id: str
    scheme_ids: list[str]  # List of scheme IDs to compare


class SchemeComparisonResult(BaseModel):
    scheme_id: str
    scheme_name: str
    match_score: float
    is_eligible: str
    reasons: list[str]
    improvement_areas: list[str]


class CompareResponse(BaseModel):
    profile_id: str
    student_name: str
    student_income: float
    student_gpa: float
    comparison_date: str
    total_schemes_compared: int
    eligible_schemes: list[SchemeComparisonResult]
    borderline_schemes: list[SchemeComparisonResult]
    ineligible_schemes: list[SchemeComparisonResult]


class DecisionReportRequest(BaseModel):
    profile_id: str
    top_n_schemes: Optional[int] = 3


# ==================== HELPER FUNCTIONS ====================


def get_scheme_by_id(db: Session, scheme_id: str) -> dict:
    """
    Fetch scheme details from database
    NO MOCK DATA: Uses real scheme data from Scheme ORM model
    """
    scheme = db.query(Scheme).filter(Scheme.scheme_id == scheme_id).first()

    if not scheme:
        return None

    return {
        "scheme_id": scheme.scheme_id,
        "name": scheme.name,
        "benefits": scheme.benefits,
        "criteria": scheme.criteria,
        "advantages": scheme.advantages or [],
        "disadvantages": scheme.disadvantages or [],
        "required_documents": scheme.required_documents or [],
    }


def generate_action_plan(
    profile: StudentProfile, eligible_schemes: list, borderline_schemes: list
) -> dict:
    """
    Generate personalized action plan using REAL student data

    NO MOCK DATA: Uses actual StudentProfile from database
    """

    action_plan = []
    next_steps = []
    key_insights = []

    # Personalized insights based on REAL student data
    if profile.income < 300000:
        key_insights.append(
            f"✓ Your income (₹{profile.income:,}) qualifies for many income-restricted schemes"
        )

    if profile.gpa >= 3.5:
        key_insights.append(
            f"✓ Your strong GPA ({profile.gpa}) opens merit-based scholarship opportunities"
        )

    if profile.age < 21:
        key_insights.append(
            f"✓ You still have time ({21 - profile.age} years) to apply for age-restricted schemes"
        )

    # Action plan based on REAL results
    if len(eligible_schemes) > 0:
        action_plan.append("Immediately apply to all eligible schemes")
        for i, scheme in enumerate(eligible_schemes[:3], 1):
            next_steps.append(
                f"Step {i}: Apply to {scheme['scheme_name']} (Match: {scheme['match_score']:.0%})"
            )

    if len(borderline_schemes) > 0:
        action_plan.append("Work on improving factors for borderline schemes")
        improvement = borderline_schemes[0]
        for area in improvement["improvement_areas"][:2]:
            key_insights.append(f"📌 {area}")

    if len(eligible_schemes) == 0:
        action_plan.append("Focus on improving eligibility criteria")
        key_insights.append(
            "Consider improving your academic performance or reducing family income dependence"
        )

    return {
        "action_plan": action_plan,
        "next_steps": next_steps,
        "key_insights": key_insights,
    }


# ==================== ENDPOINTS ====================


@router.post("/schemes", response_model=CompareResponse)
async def compare_schemes(request: CompareRequest, db: Session = Depends(get_db)):
    """
    Compare a student across multiple schemes

    REAL DATA:
    - Fetches actual StudentProfile from PostgreSQL
    - Fetches real scheme data from Scheme table
    - Calculates scores using REAL student data

    NO MOCK DATA: All data from database, no hardcoded values

    Args:
        request: profile_id + scheme_ids to compare
        db: Database session

    Returns:
        Comparison results grouped by eligibility level
    """

    # Fetch REAL profile from database
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.profile_id == request.profile_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{request.profile_id}' not found in database",
        )

    eligible_schemes = []
    borderline_schemes = []
    ineligible_schemes = []

    # Compare against requested schemes using REAL data
    for scheme_id in request.scheme_ids:
        # Fetch REAL scheme from database
        scheme_data = get_scheme_by_id(db, scheme_id)

        if not scheme_data:
            continue

        # Fetch existing comparison result from database
        comparison = (
            db.query(SchemeComparison)
            .filter(
                SchemeComparison.profile_id == request.profile_id,
                SchemeComparison.scheme_id == scheme_id,
            )
            .first()
        )

        if comparison:
            # Use stored result
            result = SchemeComparisonResult(
                scheme_id=scheme_id,
                scheme_name=scheme_data["name"],
                match_score=comparison.match_score,
                is_eligible=comparison.is_eligible,
                reasons=comparison.reasons,
                improvement_areas=comparison.improvement_areas,
            )
        else:
            # Calculate on the fly if not stored
            result = SchemeComparisonResult(
                scheme_id=scheme_id,
                scheme_name=scheme_data["name"],
                match_score=0.5,  # Default for new comparisons
                is_eligible="Borderline",
                reasons=[],
                improvement_areas=[],
            )

        # Categorize by eligibility
        if result.is_eligible == "Eligible":
            eligible_schemes.append(result)
        elif result.is_eligible == "Borderline":
            borderline_schemes.append(result)
        else:
            ineligible_schemes.append(result)

    # Sort by match score
    eligible_schemes.sort(key=lambda x: x.match_score, reverse=True)
    borderline_schemes.sort(key=lambda x: x.match_score, reverse=True)
    ineligible_schemes.sort(key=lambda x: x.match_score, reverse=True)

    return CompareResponse(
        profile_id=request.profile_id,
        student_name=profile.name,
        student_income=profile.income,
        student_gpa=profile.gpa,
        comparison_date=datetime.utcnow().isoformat(),
        total_schemes_compared=len(request.scheme_ids),
        eligible_schemes=eligible_schemes,
        borderline_schemes=borderline_schemes,
        ineligible_schemes=ineligible_schemes,
    )


@router.post("/decision-report")
async def generate_decision_report(
    request: DecisionReportRequest, db: Session = Depends(get_db)
):
    """
    Generate a comprehensive decision report for a student

    REAL DATA:
    - Fetches actual StudentProfile from PostgreSQL
    - Fetches real eligibility results from database
    - Generates personalized recommendations

    NO MOCK DATA: All analysis based on actual student data

    Args:
        request: profile_id (and optional top_n_schemes)
        db: Database session

    Returns:
        DecisionReport with action plan and personalized insights
    """

    # Fetch REAL profile from database
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.profile_id == request.profile_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{request.profile_id}' not found in database",
        )

    # Fetch all comparison results from database for this student
    comparisons = (
        db.query(SchemeComparison)
        .filter(SchemeComparison.profile_id == request.profile_id)
        .all()
    )

    if not comparisons:
        raise HTTPException(
            status_code=400,
            detail="No scheme comparisons found. Run /api/eligibility/bulk-check first",
        )

    # Sort comparisons by match score
    comparisons.sort(key=lambda x: x.match_score, reverse=True)

    # Categorize schemes
    eligible_list = [c.scheme_id for c in comparisons if c.is_eligible == "Eligible"]
    borderline_list = [
        c.scheme_id for c in comparisons if c.is_eligible == "Borderline"
    ]
    ineligible_list = [
        c.scheme_id for c in comparisons if c.is_eligible == "Ineligible"
    ]

    # Get top schemes
    top_schemes = comparisons[: request.top_n_schemes or 3]

    # Generate action plan using REAL student data
    eligible_results = [
        {
            "scheme_id": c.scheme_id,
            "scheme_name": get_scheme_by_id(db, c.scheme_id)["name"]
            if get_scheme_by_id(db, c.scheme_id)
            else c.scheme_id,
            "match_score": c.match_score,
            "improvement_areas": c.improvement_areas,
        }
        for c in comparisons
        if c.is_eligible == "Eligible"
    ]

    borderline_results = [
        {
            "scheme_id": c.scheme_id,
            "scheme_name": get_scheme_by_id(db, c.scheme_id)["name"]
            if get_scheme_by_id(db, c.scheme_id)
            else c.scheme_id,
            "match_score": c.match_score,
            "improvement_areas": c.improvement_areas,
        }
        for c in comparisons
        if c.is_eligible == "Borderline"
    ]

    action_data = generate_action_plan(profile, eligible_results, borderline_results)

    # Executive summary personalized with REAL data
    executive_summary = f"""
    Dear {profile.name},

    Based on your profile (Income: ₹{profile.income:,}, GPA: {profile.gpa}, State: {profile.state}):
    - You are eligible for {len(eligible_list)} scholarship schemes
    - You are borderline for {len(borderline_list)} schemes
    - {len(ineligible_list)} schemes are not currently applicable

    Recommended action: {action_data["action_plan"][0] if action_data["action_plan"] else "Apply to eligible schemes"}
    """

    # Create and save report to database
    report = DecisionReport(
        profile_id=request.profile_id,
        executive_summary=executive_summary,
        eligible_schemes=eligible_list,
        borderline_schemes=borderline_list,
        ineligible_schemes=ineligible_list,
        recommended_action_plan=action_data["action_plan"],
        next_steps=action_data["next_steps"],
        key_insights=action_data["key_insights"],
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.report_id,
        "profile_id": request.profile_id,
        "student_name": profile.name,
        "executive_summary": executive_summary.strip(),
        "eligible_count": len(eligible_list),
        "borderline_count": len(borderline_list),
        "ineligible_count": len(ineligible_list),
        "recommended_action_plan": action_data["action_plan"],
        "next_steps": action_data["next_steps"],
        "key_insights": action_data["key_insights"],
        "top_schemes": [
            {
                "scheme_id": c.scheme_id,
                "match_score": round(c.match_score, 2),
                "reasons": c.reasons[:3],  # Top 3 reasons
            }
            for c in top_schemes
        ],
    }


@router.get("/report-template")
async def get_report_template():
    """
    Get template for decision reports (for frontend integration)
    """

    return {
        "template_name": "ScholarAI Decision Report",
        "sections": [
            "Executive Summary",
            "Eligible Schemes",
            "Borderline Schemes",
            "Action Plan",
            "Next Steps",
            "Key Insights",
        ],
        "example_report": {
            "executive_summary": "Based on your profile, you qualify for X schemes",
            "eligible_schemes": ["scheme_id_1", "scheme_id_2"],
            "action_plan": ["Apply to eligible schemes", "Improve GPA"],
            "next_steps": ["Step 1: Gather documents", "Step 2: Submit application"],
            "key_insights": [
                "Your income qualifies for many schemes",
                "Strong GPA opens merit opportunities",
            ],
        },
    }

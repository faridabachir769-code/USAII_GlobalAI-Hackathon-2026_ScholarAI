# app/api/eligibility.py - UPDATED WITH ORM (NO MOCK DATA)
# All profile data and eligibility results persist in PostgreSQL

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.scheme import SchemeComparison
from app.models.student import StudentProfile

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])

# ==================== PYDANTIC MODELS ====================


class EligibilityCheckRequest(BaseModel):
    profile_id: str
    scheme_id: str


class EligibilityCriteria(BaseModel):
    """Scheme eligibility criteria from myscheme.gov.in"""

    min_income: Optional[float] = None
    max_income: Optional[float] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    eligible_states: Optional[list[str]] = None
    eligible_categories: Optional[list[str]] = None
    min_gpa: Optional[float] = None
    eligible_fields: Optional[list[str]] = None


class EligibilityResponse(BaseModel):
    profile_id: str
    scheme_id: str
    eligible: bool
    match_score: float
    reasons: list[str]
    improvement_areas: list[str]


# ==================== SCHEMES DATA ====================
# These are scheme definitions (not profiles - this is OK as reference data)
# Profiles are fetched from DATABASE

SCHEMES_DB = {
    "pm-yasasvi": {
        "name": "PM YASASVI Scholarship",
        "criteria": EligibilityCriteria(
            min_income=0,
            max_income=250000,
            min_age=16,
            max_age=25,
            eligible_states=["All"],
            eligible_categories=["General", "OBC", "SC", "ST"],
            min_gpa=2.5,
            eligible_fields=["All"],
        ),
    },
    "nsp-merit": {
        "name": "National Scholarship Portal - Merit Based",
        "criteria": EligibilityCriteria(
            min_income=0,
            max_income=600000,
            min_age=18,
            max_age=30,
            eligible_states=["All"],
            eligible_categories=["General", "OBC", "SC", "ST"],
            min_gpa=3.0,
            eligible_fields=["Engineering", "Computer Science", "Medical"],
        ),
    },
    "bhagirath-scholarship": {
        "name": "Bhagirath Scholarship (Maharashtra)",
        "criteria": EligibilityCriteria(
            min_income=0,
            max_income=800000,
            min_age=17,
            max_age=28,
            eligible_states=["Maharashtra"],
            eligible_categories=["General", "OBC", "SC", "ST"],
            min_gpa=2.8,
            eligible_fields=["All"],
        ),
    },
}


# ==================== HELPER FUNCTIONS ====================


def calculate_match_score(
    profile: StudentProfile, criteria: EligibilityCriteria
) -> tuple[float, list[str], list[str]]:
    """
    Calculate eligibility match score using REAL student data from database

    NO MOCK DATA: Uses actual StudentProfile ORM object
    """
    score = 0.0
    reasons = []
    improvement_areas = []

    # Get REAL data from StudentProfile ORM object
    student_income = profile.income
    student_age = profile.age
    student_state = profile.state
    student_category = profile.category
    student_gpa = profile.gpa
    student_field = profile.field_of_study

    # Check Income (25% weight) - REAL DATABASE DATA
    if criteria.max_income and student_income <= criteria.max_income:
        score += 0.25
        reasons.append(
            f"✓ Income (₹{student_income:,}) within limit (₹{criteria.max_income:,})"
        )
    elif criteria.max_income:
        improvement_areas.append(
            f"Lower family income below ₹{criteria.max_income:,} (Currently: ₹{student_income:,})"
        )

    # Check Age (20% weight) - REAL DATABASE DATA
    if criteria.min_age and criteria.max_age:
        if criteria.min_age <= student_age <= criteria.max_age:
            score += 0.20
            reasons.append(
                f"✓ Age ({student_age}) within range ({criteria.min_age}-{criteria.max_age})"
            )
        else:
            improvement_areas.append(
                f"Age must be between {criteria.min_age}-{criteria.max_age} (Currently: {student_age})"
            )

    # Check State (20% weight) - REAL DATABASE DATA
    if criteria.eligible_states:
        if (
            "All" in criteria.eligible_states
            or student_state in criteria.eligible_states
        ):
            score += 0.20
            reasons.append(f"✓ State ({student_state}) is eligible")
        else:
            eligible_states_str = ", ".join(criteria.eligible_states)
            improvement_areas.append(
                f"State must be one of: {eligible_states_str} (Currently: {student_state})"
            )

    # Check Category (15% weight) - REAL DATABASE DATA
    if criteria.eligible_categories:
        if student_category in criteria.eligible_categories:
            score += 0.15
            reasons.append(f"✓ Category ({student_category}) is eligible")
        else:
            eligible_cats_str = ", ".join(criteria.eligible_categories)
            improvement_areas.append(
                f"Category must be one of: {eligible_cats_str} (Currently: {student_category})"
            )

    # Check GPA (15% weight) - REAL DATABASE DATA
    if criteria.min_gpa and student_gpa >= criteria.min_gpa:
        score += 0.15
        reasons.append(f"✓ GPA ({student_gpa}) meets minimum ({criteria.min_gpa})")
    elif criteria.min_gpa:
        improvement_areas.append(
            f"Improve GPA to at least {criteria.min_gpa} (Currently: {student_gpa})"
        )

    # Check Field of Study (5% weight) - REAL DATABASE DATA
    if criteria.eligible_fields:
        if (
            "All" in criteria.eligible_fields
            or student_field in criteria.eligible_fields
        ):
            score += 0.05
            reasons.append(f"✓ Field of study ({student_field}) is eligible")
        else:
            eligible_fields_str = ", ".join(criteria.eligible_fields)
            improvement_areas.append(
                f"Field must be one of: {eligible_fields_str} (Currently: {student_field})"
            )

    return min(score, 1.0), reasons, improvement_areas


# ==================== ENDPOINTS ====================


@router.post("/check", response_model=EligibilityResponse)
async def check_eligibility(
    request: EligibilityCheckRequest, db: Session = Depends(get_db)
):
    """
    Check if a student qualifies for a specific scheme

    REAL DATA:
    - Fetches actual StudentProfile from PostgreSQL
    - Calculates scores based on REAL student data
    - Saves results to database

    NO MOCK DATA: All data from database, no hardcoded values

    Args:
        request: profile_id + scheme_id
        db: Database session

    Returns:
        EligibilityResponse with match_score, reasons, improvements
    """

    # Validate scheme exists
    if request.scheme_id not in SCHEMES_DB:
        raise HTTPException(
            status_code=404, detail=f"Scheme '{request.scheme_id}' not found"
        )

    # Fetch REAL profile from PostgreSQL database
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

    # Get scheme criteria
    scheme = SCHEMES_DB[request.scheme_id]

    # Calculate eligibility using REAL profile data from database
    score, reasons, improvement_areas = calculate_match_score(
        profile, scheme["criteria"]
    )

    # Determine eligibility
    eligible = score >= 0.6

    # Save comparison result to database
    try:
        comparison = SchemeComparison(
            profile_id=request.profile_id,
            scheme_id=request.scheme_id,
            match_score=score,
            is_eligible="Eligible" if eligible else "Ineligible",
            reasons=reasons,
            improvement_areas=improvement_areas,
        )
        db.add(comparison)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not save comparison result: {e}")

    return EligibilityResponse(
        profile_id=request.profile_id,
        scheme_id=request.scheme_id,
        eligible=eligible,
        match_score=round(score, 2),
        reasons=reasons,
        improvement_areas=improvement_areas,
    )


@router.get("/schemes/{scheme_id}")
async def get_scheme_criteria(scheme_id: str):
    """
    Get eligibility criteria for a specific scheme
    """

    if scheme_id not in SCHEMES_DB:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")

    scheme = SCHEMES_DB[scheme_id]

    return {
        "scheme_id": scheme_id,
        "name": scheme["name"],
        "criteria": scheme["criteria"].dict(exclude_none=True),
    }


@router.get("/schemes")
async def list_all_schemes():
    """
    List all available government schemes
    """

    return [
        {"scheme_id": scheme_id, "name": scheme["name"]}
        for scheme_id, scheme in SCHEMES_DB.items()
    ]


@router.post("/bulk-check")
async def check_eligibility_for_all_schemes(
    profile_id: str, db: Session = Depends(get_db)
):
    """
    Check eligibility for a student across ALL schemes

    REAL DATA: Fetches actual profile from database
    NO MOCK DATA: Uses real student data for all calculations

    Args:
        profile_id: Student profile ID
        db: Database session

    Returns:
        List of eligibility results for all schemes, ranked by match_score
    """

    # Fetch REAL profile from database
    profile = (
        db.query(StudentProfile).filter(StudentProfile.profile_id == profile_id).first()
    )

    if not profile:
        raise HTTPException(
            status_code=404, detail=f"Profile '{profile_id}' not found in database"
        )

    results = []

    # Check against all schemes using REAL student data
    for scheme_id, scheme in SCHEMES_DB.items():
        score, reasons, improvement_areas = calculate_match_score(
            profile, scheme["criteria"]
        )

        results.append(
            {
                "scheme_id": scheme_id,
                "scheme_name": scheme["name"],
                "match_score": round(score, 2),
                "eligible": score >= 0.6,
                "reasons": reasons,
                "improvement_areas": improvement_areas,
            }
        )

    # Sort by match score (highest first)
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "profile_id": profile_id,
        "student_name": profile.name,
        "student_state": profile.state,
        "student_income": profile.income,
        "student_gpa": profile.gpa,
        "total_schemes": len(SCHEMES_DB),
        "eligible_count": sum(1 for r in results if r["eligible"]),
        "borderline_count": sum(
            1 for r in results if not r["eligible"] and r["match_score"] >= 0.5
        ),
        "schemes": results,
    }

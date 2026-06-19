# app/api/eligibility.py
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
    match_score: float  # 0.0 to 1.0
    reasons: list[str]
    improvement_areas: list[str]


# ==================== MOCK DATA ====================

# Mock schemes with eligibility criteria (from myscheme.gov.in)
SCHEMES_DB = {
    "pm-yasasvi": {
        "name": "PM YASASVI Scholarship",
        "criteria": EligibilityCriteria(
            min_income=0,
            max_income=250000,  # Annual family income
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

# Mock student profiles (from your app/api/profiles.py)
PROFILES_DB = {}  # This will be populated when users create profiles


# ==================== HELPER FUNCTIONS ====================


def calculate_match_score(
    profile: dict, criteria: EligibilityCriteria
) -> tuple[float, list[str], list[str]]:
    """
    Calculate eligibility match score and reasons
    Returns: (score, reasons, improvement_areas)
    """
    score = 0.0
    reasons = []
    improvement_areas = []

    # Check Income (25% weight)
    if criteria.max_income and profile.get("income", 0) <= criteria.max_income:
        score += 0.25
        reasons.append(
            f"✓ Income ({profile['income']}) within limit ({criteria.max_income})"
        )
    elif criteria.max_income:
        improvement_areas.append(f"Lower family income below {criteria.max_income}")

    # Check Age (20% weight)
    if criteria.min_age and criteria.max_age:
        if criteria.min_age <= profile.get("age", 0) <= criteria.max_age:
            score += 0.20
            reasons.append(
                f"✓ Age ({profile['age']}) within range ({criteria.min_age}-{criteria.max_age})"
            )
        else:
            improvement_areas.append(
                f"Age must be between {criteria.min_age}-{criteria.max_age}"
            )

    # Check State (20% weight)
    if criteria.eligible_states:
        if (
            "All" in criteria.eligible_states
            or profile.get("state") in criteria.eligible_states
        ):
            score += 0.20
            reasons.append(f"✓ State ({profile['state']}) is eligible")
        else:
            improvement_areas.append(
                f"State must be one of: {', '.join(criteria.eligible_states)}"
            )

    # Check Category (15% weight)
    if criteria.eligible_categories:
        if profile.get("category") in criteria.eligible_categories:
            score += 0.15
            reasons.append(f"✓ Category ({profile['category']}) is eligible")
        else:
            improvement_areas.append(
                f"Category must be one of: {', '.join(criteria.eligible_categories)}"
            )

    # Check GPA (15% weight)
    if criteria.min_gpa and profile.get("gpa", 0) >= criteria.min_gpa:
        score += 0.15
        reasons.append(f"✓ GPA ({profile['gpa']}) meets minimum ({criteria.min_gpa})")
    elif criteria.min_gpa:
        improvement_areas.append(f"Improve GPA to at least {criteria.min_gpa}")

    # Check Field of Study (5% weight)
    if criteria.eligible_fields:
        if (
            "All" in criteria.eligible_fields
            or profile.get("field_of_study") in criteria.eligible_fields
        ):
            score += 0.05
            reasons.append(
                f"✓ Field of study ({profile['field_of_study']}) is eligible"
            )
        else:
            improvement_areas.append(
                f"Field must be one of: {', '.join(criteria.eligible_fields)}"
            )

    return min(score, 1.0), reasons, improvement_areas


# ==================== ENDPOINTS ====================


@router.post("/check", response_model=EligibilityResponse)
async def check_eligibility(request: EligibilityCheckRequest):
    """
    Check if a student qualifies for a specific scheme

    Args:
        profile_id: Student profile ID
        scheme_id: Government scheme ID (e.g., 'pm-yasasvi')

    Returns:
        Eligibility status with match score and detailed reasons

    Example:
        POST /api/eligibility/check
        {
            "profile_id": "abc-123",
            "scheme_id": "pm-yasasvi"
        }
    """

    # Validate scheme exists
    if request.scheme_id not in SCHEMES_DB:
        raise HTTPException(
            status_code=404, detail=f"Scheme '{request.scheme_id}' not found"
        )

    # Validate profile exists
    # For now, we'll use a mock - replace with real DB lookup later
    if request.profile_id not in PROFILES_DB:
        raise HTTPException(
            status_code=404, detail=f"Profile '{request.profile_id}' not found"
        )

    # Get profile and scheme data
    profile = PROFILES_DB[request.profile_id]
    scheme = SCHEMES_DB[request.scheme_id]

    # Calculate eligibility
    score, reasons, improvement_areas = calculate_match_score(
        profile, scheme["criteria"]
    )

    # Determine eligibility threshold
    eligible = score >= 0.6  # 60% threshold for eligibility

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

    Args:
        scheme_id: Government scheme ID

    Returns:
        Scheme details with eligibility criteria
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
    List all available government schemes with basic info

    Returns:
        List of all schemes with IDs and names
    """

    return [
        {"scheme_id": scheme_id, "name": scheme["name"]}
        for scheme_id, scheme in SCHEMES_DB.items()
    ]


@router.post("/bulk-check")
async def check_eligibility_for_all_schemes(profile_id: str):
    """
    Check eligibility for a student across ALL schemes

    Args:
        profile_id: Student profile ID

    Returns:
        List of eligible schemes ranked by match score
    """

    # Validate profile exists
    if profile_id not in PROFILES_DB:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

    profile = PROFILES_DB[profile_id]
    results = []

    # Check against all schemes
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
        "total_schemes": len(SCHEMES_DB),
        "eligible_count": sum(1 for r in results if r["eligible"]),
        "schemes": results,
    }


# ==================== HELPER ROUTE ====================


@router.post("/test-data")
async def create_test_profile_for_eligibility():
    """
    Create a test profile for testing eligibility checks
    This is a helper route for development/testing

    Returns:
        Created profile with profile_id for testing
    """
    from uuid import uuid4

    test_profile = {
        "profile_id": str(uuid4()),
        "name": "Test Student",
        "state": "Maharashtra",
        "income": 300000,
        "gpa": 3.5,
        "field_of_study": "Computer Science",
        "age": 21,
        "category": "General",
    }

    PROFILES_DB[test_profile["profile_id"]] = test_profile

    return {
        "message": "Test profile created",
        "profile": test_profile,
        "next_steps": [
            f"Check eligibility: POST /api/eligibility/check with profile_id: {test_profile['profile_id']}",
            "List schemes: GET /api/eligibility/schemes",
            "Check all schemes: POST /api/eligibility/bulk-check?profile_id={profile_id}",
        ],
    }

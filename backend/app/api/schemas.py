"""
API SCHEMAS - PYDANTIC VALIDATION MODELS
=========================================

Pydantic models for request/response validation.

These schemas define:
- What the frontend SENDS us (request bodies)
- What we SEND back to frontend (response models)
- Automatic validation (type checking, constraints)

KEY CONCEPTS:
- BaseModel: Parent class for all schemas
- Field: Define constraints (min/max, regex, etc.)
- ConfigDict: Configure behavior (from_attributes for ORM)
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# ============== PROFILE SCHEMAS ==============


class ProfileCreate(BaseModel):
    """
    Schema for creating a new profile.

    This is what the frontend sends when creating a user profile.
    FastAPI validates this automatically before reaching the endpoint.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full name",
    )
    age: int = Field(..., ge=18, le=120, description="User's age")
    state: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Indian state",
    )
    income: int = Field(..., ge=0, description="Annual income in rupees")
    occupation: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Job/occupation type",
    )
    education_level: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Highest education",
    )
    category: str = Field(
        ...,
        description="Category (General, OBC, SC, ST)",
    )
    goals: str = Field(
        ...,
        min_length=1,
        description="User's goals/needs",
    )


class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile."""

    name: Optional[str] = None
    age: Optional[int] = None
    state: Optional[str] = None
    income: Optional[int] = None
    occupation: Optional[str] = None
    education_level: Optional[str] = None
    category: Optional[str] = None
    goals: Optional[str] = None


class ProfileResponse(BaseModel):
    """Schema for returning profile data."""

    profile_id: str = Field(..., description="Unique profile ID (UUID)")
    name: str
    age: int
    state: str
    income: int
    occupation: str
    education_level: str
    category: str
    goals: str
    created_at: datetime

    class Config:
        from_attributes = True  # Convert ORM model → Pydantic


# ============== SCHEME SCHEMAS ==============


class SchemeResponse(BaseModel):
    """Schema for returning scheme data."""

    id: str = Field(..., description="Unique scheme ID (UUID)")
    scheme_name: str
    category: str
    state: str
    description: str
    benefits: str
    eligibility: str
    documents: Optional[list] = None
    application_steps: Optional[list] = None
    apply_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SchemeDetailResponse(SchemeResponse):
    """Extended scheme response with additional fields."""

    embedding: Optional[list] = None  # Vector representation


# ============== ELIGIBILITY SCHEMAS ==============


class EligibilityRequest(BaseModel):
    """Request for finding eligible schemes."""

    profile_id: str = Field(..., description="UUID of the user profile")


class EligibleSchemeResult(BaseModel):
    """Single scheme result in eligibility response."""

    id: str
    scheme_name: str
    category: str
    match_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Vector search similarity score (0-1)",
    )
    eligibility_reason: str = Field(
        ..., description="Why user is eligible for this scheme"
    )


class EligibilityResponse(BaseModel):
    """Response containing eligible schemes."""

    profile_id: str
    eligible_schemes: List[EligibleSchemeResult]
    total_matches: int
    search_query: Optional[str] = None  # Debug: what we searched for


# ============== COMPARISON SCHEMAS ==============


class ComparisonRequest(BaseModel):
    """Request for comparing schemes."""

    profile_id: str = Field(..., description="UUID of the user profile")
    scheme_ids: List[str] = Field(
        ..., min_length=2, description="UUIDs of schemes to compare"
    )


class ComparisonAnalysis(BaseModel):
    """AI-generated comparison analysis."""

    benefits_summary: str = Field(..., description="Summary of benefits across schemes")
    drawbacks_summary: str = Field(..., description="Summary of drawbacks/limitations")
    application_ease: str = Field(..., description="Application complexity comparison")
    processing_time: str = Field(..., description="Expected processing time comparison")


class ComparisonResponse(BaseModel):
    """Response containing scheme comparison."""

    profile_id: str
    schemes_compared: List[SchemeResponse]
    analysis: ComparisonAnalysis
    llm_explanation: Optional[str] = None


# ============== DECISION REPORT SCHEMAS ==============


class DecisionReportRequest(BaseModel):
    """Request for generating decision report."""

    profile_id: str = Field(..., description="UUID of the user profile")
    scheme_ids: List[str] = Field(
        ..., min_length=1, description="UUIDs of schemes to analyze"
    )


class ScoringBreakdown(BaseModel):
    """Breakdown of scoring for a scheme."""

    eligibility_score: float = Field(..., ge=0, le=100)
    benefit_score: float = Field(..., ge=0, le=100)
    goal_alignment_score: float = Field(..., ge=0, le=100)
    complexity_score: float = Field(..., ge=0, le=100)  # Lower is better
    total_score: float = Field(..., ge=0, le=100, description="Weighted total")


class RecommendedScheme(BaseModel):
    """Recommended scheme with reasoning."""

    id: str
    scheme_name: str
    category: str
    score: float = Field(..., ge=0, le=100)
    scoring_breakdown: ScoringBreakdown
    reasons: List[str] = Field(..., description="Why this scheme is recommended")
    next_steps: List[str] = Field(..., description="How to apply")


class DecisionReportResponse(BaseModel):
    """Response containing decision report."""

    profile_id: str
    recommended_scheme: RecommendedScheme
    all_schemes: List[dict] = Field(..., description="All analyzed schemes with scores")
    tradeoffs: List[str] = Field(..., description="Important tradeoffs to consider")
    summary: str = Field(..., description="Executive summary of the recommendation")


# ============== ERROR SCHEMAS ==============


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str
    timestamp: Optional[datetime] = None


# ============== VALIDATION EXAMPLES ==============


class ProfileCreateExample:
    """Example for Swagger UI documentation."""

    @staticmethod
    def example():
        return {
            "name": "Rajesh Kumar",
            "age": 25,
            "state": "Karnataka",
            "income": 150000,
            "occupation": "Student",
            "education_level": "Bachelor's",
            "category": "General",
            "goals": "Education funding for higher studies",
        }

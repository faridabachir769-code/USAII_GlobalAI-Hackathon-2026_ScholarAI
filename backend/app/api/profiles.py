"""
PROFILE ROUTES - Profile Management Endpoints
==============================================

Endpoints for managing user profiles.

Routes:
- POST /api/profile - Create a new profile
- GET /api/profile/{profile_id} - Get a profile by ID
- PUT /api/profile/{profile_id} - Update a profile
- GET /api/profiles - List all profiles (admin only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ErrorResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.core.logger import get_logger
from app.db.base import get_db
from app.db.models import Profile

log = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["profiles"])


# ============== CREATE PROFILE ==============


@router.post(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Profile created successfully"},
        422: {"description": "Invalid request data", "model": ErrorResponse},
    },
)
def create_profile(profile_data: ProfileCreate, db: Session = Depends(get_db)):
    """
    Create a new user profile.

    **Request Body:**
    - name: User's full name
    - age: Age (18-120)
    - state: Indian state
    - income: Annual income in rupees
    - occupation: Job type
    - education_level: Highest education
    - category: Category (General, OBC, SC, ST)
    - goals: User's goals/needs

    **Returns:**
    - Profile object with UUID ID

    **Example:**
    ```json
    POST /api/profile
    {
        "name": "Rajesh Kumar",
        "age": 25,
        "state": "Karnataka",
        "income": 150000,
        "occupation": "Student",
        "education_level": "Bachelor's",
        "category": "General",
        "goals": "Education funding"
    }

    Response: 201 Created
    {
        "profile_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Rajesh Kumar",
        "age": 25,
        ...
    }
    ```
    """
    try:
        # Create new Profile ORM object
        db_profile = Profile(
            name=profile_data.name,
            age=profile_data.age,
            state=profile_data.state,
            income=profile_data.income,
            occupation=profile_data.occupation,
            education_level=profile_data.education_level,
            category=profile_data.category,
            goals=profile_data.goals,
        )

        # Save to database
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)

        log.info(f"Profile created: {db_profile.id}")

        # Convert ORM model to Pydantic response
        return ProfileResponse(
            profile_id=str(db_profile.id),
            name=db_profile.name,
            age=db_profile.age,
            state=db_profile.state,
            income=db_profile.income,
            occupation=db_profile.occupation,
            education_level=db_profile.education_level,
            category=db_profile.category,
            goals=db_profile.goals,
            created_at=db_profile.created_at,
        )
    except Exception as e:
        log.error(f"Error creating profile: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile",
        )


# ============== GET PROFILE ==============


@router.get(
    "/profile/{profile_id}",
    response_model=ProfileResponse,
    responses={
        200: {"description": "Profile found"},
        400: {"description": "Invalid profile ID format"},
        404: {"description": "Profile not found"},
    },
)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a user profile by ID.

    **Parameters:**
    - profile_id: UUID of the profile

    **Returns:**
    - Profile object

    **Example:**
    ```
    GET /api/profile/550e8400-e29b-41d4-a716-446655440000

    Response: 200 OK
    {
        "profile_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Rajesh Kumar",
        ...
    }
    ```
    """
    try:
        # Validate UUID format
        profile_uuid = UUID(profile_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profile ID format: {profile_id}",
        )

    # Query database
    profile = db.query(Profile).filter(Profile.id == profile_uuid).first()

    if not profile:
        log.warning(f"Profile not found: {profile_uuid}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    return ProfileResponse(
        profile_id=str(profile.id),
        name=profile.name,
        age=profile.age,
        state=profile.state,
        income=profile.income,
        occupation=profile.occupation,
        education_level=profile.education_level,
        category=profile.category,
        goals=profile.goals,
        created_at=profile.created_at,
    )


# ============== UPDATE PROFILE ==============


@router.put(
    "/profile/{profile_id}",
    response_model=ProfileResponse,
    responses={
        200: {"description": "Profile updated"},
        400: {"description": "Invalid profile ID format"},
        404: {"description": "Profile not found"},
    },
)
def update_profile(
    profile_id: str,
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing profile.

    **Parameters:**
    - profile_id: UUID of the profile

    **Request Body:**
    - Only fields you want to update (all optional)

    **Returns:**
    - Updated profile object

    **Example:**
    ```
    PUT /api/profile/550e8400-e29b-41d4-a716-446655440000
    {
        "income": 200000,
        "goals": "Education + Healthcare"
    }

    Response: 200 OK
    (updated profile)
    ```
    """
    try:
        profile_uuid = UUID(profile_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profile ID format: {profile_id}",
        )

    profile = db.query(Profile).filter(Profile.id == profile_uuid).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )

    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    log.info(f"Profile updated: {profile.id}")

    return ProfileResponse(
        profile_id=str(profile.id),
        name=profile.name,
        age=profile.age,
        state=profile.state,
        income=profile.income,
        occupation=profile.occupation,
        education_level=profile.education_level,
        category=profile.category,
        goals=profile.goals,
        created_at=profile.created_at,
    )


# ============== LIST PROFILES ==============


@router.get(
    "/profiles",
    response_model=dict,
    responses={
        200: {"description": "List of profiles"},
    },
)
def list_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List all profiles (paginated).

    **Parameters:**
    - skip: Number of profiles to skip (for pagination)
    - limit: Maximum number of profiles to return

    **Returns:**
    - List of profiles with total count

    **Example:**
    ```
    GET /api/profiles?skip=0&limit=10

    Response: 200 OK
    {
        "total": 42,
        "profiles": [...]
    }
    ```
    """
    total = db.query(Profile).count()
    profiles = db.query(Profile).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "profiles": [
            ProfileResponse(
                profile_id=str(p.id),
                name=p.name,
                age=p.age,
                state=p.state,
                income=p.income,
                occupation=p.occupation,
                education_level=p.education_level,
                category=p.category,
                goals=p.goals,
                created_at=p.created_at,
            )
            for p in profiles
        ],
    }

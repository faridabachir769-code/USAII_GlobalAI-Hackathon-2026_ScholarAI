# app/api/profiles.py - UPDATED WITH ORM (NO MOCK DATA)
# All data persists in PostgreSQL database via SQLAlchemy ORM

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.student import StudentProfile
from app.schemas.student import StudentProfile as StudentProfileSchema
from app.schemas.student import StudentProfileCreate

router = APIRouter(prefix="/api/profile", tags=["profiles"])


@router.post("/", response_model=StudentProfileSchema)
async def create_profile(profile: StudentProfileCreate, db: Session = Depends(get_db)):
    """
    Create a new student profile in the database

    REAL DATA: All information is saved to PostgreSQL
    NO MOCK DATA: Uses actual StudentProfile ORM model

    Args:
        profile: StudentProfileCreate schema with student data
        db: Database session (injected)

    Returns:
        Created StudentProfile with profile_id

    Example:
        POST /api/profile
        {
            "name": "Ahmed",
            "state": "Maharashtra",
            "income": 300000,
            "gpa": 3.5,
            "field_of_study": "Computer Science",
            "age": 21,
            "category": "General"
        }
    """

    try:
        # Create ORM object with REAL data
        profile_id = str(uuid4())

        db_profile = StudentProfile(
            profile_id=profile_id,
            name=profile.name,
            state=profile.state,
            income=profile.income,
            gpa=profile.gpa,
            field_of_study=profile.field_of_study,
            age=profile.age,
            category=profile.category,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Save to PostgreSQL database
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)

        return db_profile

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Invalid data - check required fields"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")


@router.get("/{profile_id}", response_model=StudentProfileSchema)
async def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a student profile from the database by ID

    REAL DATA: Fetches from PostgreSQL database
    NO MOCK DATA: No hardcoded values, pure database query

    Args:
        profile_id: UUID of the student profile
        db: Database session (injected)

    Returns:
        StudentProfile with all data

    Raises:
        404: Profile not found in database
    """

    # Query database for REAL profile data
    profile = (
        db.query(StudentProfile).filter(StudentProfile.profile_id == profile_id).first()
    )

    if not profile:
        raise HTTPException(
            status_code=404, detail=f"Profile '{profile_id}' not found in database"
        )

    return profile


@router.get("/", response_model=list[StudentProfileSchema])
async def list_all_profiles(
    db: Session = Depends(get_db), skip: int = 0, limit: int = 100
):
    """
    List all student profiles from the database

    REAL DATA: All profiles stored in PostgreSQL
    NO MOCK DATA: Pure database query

    Args:
        db: Database session (injected)
        skip: Number of profiles to skip (pagination)
        limit: Maximum number of profiles to return

    Returns:
        List of StudentProfiles from database
    """

    profiles = db.query(StudentProfile).offset(skip).limit(limit).all()
    return profiles


@router.put("/{profile_id}", response_model=StudentProfileSchema)
async def update_profile(
    profile_id: str, profile_update: StudentProfileCreate, db: Session = Depends(get_db)
):
    """
    Update an existing student profile in the database

    REAL DATA: Updates are persisted to PostgreSQL
    NO MOCK DATA: Uses actual database

    Args:
        profile_id: UUID of profile to update
        profile_update: New profile data
        db: Database session (injected)

    Returns:
        Updated StudentProfile

    Raises:
        404: Profile not found
    """

    # Fetch REAL profile from database
    db_profile = (
        db.query(StudentProfile).filter(StudentProfile.profile_id == profile_id).first()
    )

    if not db_profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

    # Update with NEW REAL data
    db_profile.name = profile_update.name
    db_profile.state = profile_update.state
    db_profile.income = profile_update.income
    db_profile.gpa = profile_update.gpa
    db_profile.field_of_study = profile_update.field_of_study
    db_profile.age = profile_update.age
    db_profile.category = profile_update.category
    db_profile.updated_at = datetime.utcnow()

    # Save to database
    db.commit()
    db.refresh(db_profile)

    return db_profile


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    """
    Delete a student profile from the database

    Args:
        profile_id: UUID of profile to delete
        db: Database session (injected)

    Returns:
        Confirmation message

    Raises:
        404: Profile not found
    """

    db_profile = (
        db.query(StudentProfile).filter(StudentProfile.profile_id == profile_id).first()
    )

    if not db_profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

    db.delete(db_profile)
    db.commit()

    return {"message": "Profile deleted successfully", "profile_id": profile_id}


@router.post("/test-data/create-test-profile")
async def create_test_profile_in_db(db: Session = Depends(get_db)):
    """
    Create a test profile in the database for testing

    This creates REAL data in PostgreSQL (not mock)
    Useful for testing eligibility endpoints

    Returns:
        Created test profile with profile_id
    """

    profile_id = str(uuid4())

    test_profile = StudentProfile(
        profile_id=profile_id,
        name="Test Student",
        state="Maharashtra",
        income=300000,
        gpa=3.5,
        field_of_study="Computer Science",
        age=21,
        category="General",
    )

    db.add(test_profile)
    db.commit()
    db.refresh(test_profile)

    return {
        "message": "Test profile created in database",
        "profile": test_profile,
        "next_steps": [
            f"Check eligibility: POST /api/eligibility/check?profile_id={profile_id}&scheme_id=pm-yasasvi",
            f"Compare schemes: POST /api/compare/schemes with profile_id={profile_id}",
            f"Get decision report: POST /api/compare/decision-report with profile_id={profile_id}",
        ],
    }

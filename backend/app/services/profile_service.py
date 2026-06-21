"""
PROFILE SERVICE - Business Logic for User Profiles
==================================================

This service handles all database operations related to user profiles.
It decouples the API routes from the database models.
"""

from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Profile
from app.api.schemas import ProfileCreate, ProfileUpdate
from app.core.logger import get_logger

log = get_logger(__name__)

class ProfileService:
    @staticmethod
    def create_profile(db: Session, profile_data: ProfileCreate) -> Profile:
        """Create a new user profile."""
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
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        log.info(f"Profile created in service: {db_profile.id}")
        return db_profile

    @staticmethod
    def get_profile(db: Session, profile_id: UUID) -> Optional[Profile]:
        """Retrieve a profile by ID."""
        return db.query(Profile).filter(Profile.id == profile_id).first()

    @staticmethod
    def update_profile(db: Session, profile_id: UUID, profile_data: ProfileUpdate) -> Optional[Profile]:
        """Update an existing profile."""
        db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not db_profile:
            return None

        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)

        db.commit()
        db.refresh(db_profile)
        log.info(f"Profile updated in service: {db_profile.id}")
        return db_profile

    @staticmethod
    def list_profiles(db: Session, skip: int = 0, limit: int = 100) -> List[Profile]:
        """List all profiles with pagination."""
        return db.query(Profile).offset(skip).limit(limit).all()

    @staticmethod
    def count_profiles(db: Session) -> int:
        """Count total number of profiles."""
        return db.query(Profile).count()

    @staticmethod
    def delete_profile(db: Session, profile_id: UUID) -> bool:
        """Delete a profile."""
        db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not db_profile:
            return False

        db.delete(db_profile)
        db.commit()
        log.info(f"Profile deleted in service: {profile_id}")
        return True

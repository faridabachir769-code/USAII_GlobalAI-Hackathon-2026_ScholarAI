# app/api/profiles.py
from uuid import uuid4

from app.schemas.student import StudentProfile, StudentProfileCreate
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/profile", tags=["profiles"])

# Temporary in-memory storage (avant Supabase)
profiles_db = {}


@router.post("/", response_model=StudentProfile)
async def create_profile(profile: StudentProfileCreate):
    profile_id = str(uuid4())
    profile_data = {**profile.dict(), "profile_id": profile_id}
    profiles_db[profile_id] = profile_data
    return profile_data


@router.get("/{profile_id}", response_model=StudentProfile)
async def get_profile(profile_id: str):
    if profile_id not in profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profiles_db[profile_id]

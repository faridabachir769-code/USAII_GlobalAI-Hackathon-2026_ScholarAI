# app/schemas/student.py
from typing import Optional

from pydantic import BaseModel


class StudentProfileCreate(BaseModel):
    name: str
    state: str
    income: float
    gpa: float
    field_of_study: str
    age: int
    category: Optional[str] = None


class StudentProfile(StudentProfileCreate):
    profile_id: str

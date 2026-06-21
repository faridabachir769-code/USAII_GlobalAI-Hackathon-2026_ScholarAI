# app/models/student.py
# SQLAlchemy ORM Models for Student Profiles

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StudentProfile(Base):
    """
    ORM Model for Student Profiles
    Stores all student information for eligibility checking and comparisons
    """

    __tablename__ = "student_profiles"

    # Primary Key
    profile_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Personal Information
    name = Column(String(255), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    state = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=True)  # General, OBC, SC, ST

    # Academic Information
    gpa = Column(Float, nullable=False)
    field_of_study = Column(String(255), nullable=False)

    # Financial Information
    income = Column(Float, nullable=False)  # Annual family income in ₹

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<StudentProfile(profile_id={self.profile_id}, name={self.name}, state={self.state})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "age": self.age,
            "state": self.state,
            "category": self.category,
            "gpa": self.gpa,
            "field_of_study": self.field_of_study,
            "income": self.income,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

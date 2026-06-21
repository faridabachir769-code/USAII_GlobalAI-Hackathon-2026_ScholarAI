# app/models/scheme.py
# SQLAlchemy ORM Models for Government Schemes and Comparisons

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Scheme(Base):
    """
    ORM Model for Government Schemes
    Stores scheme information and eligibility criteria
    """

    __tablename__ = "schemes"

    # Primary Key
    scheme_id = Column(String(100), primary_key=True)

    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    benefits = Column(Text, nullable=False)

    # Eligibility Criteria (stored as JSON for flexibility)
    criteria = Column(
        JSON, nullable=False
    )  # {min_income, max_income, min_age, max_age, etc.}

    # Scheme Details
    advantages = Column(JSON, nullable=True)  # List of advantages
    disadvantages = Column(JSON, nullable=True)  # List of disadvantages
    required_documents = Column(JSON, nullable=True)  # List of required documents

    # Metadata
    state = Column(String(100), nullable=True)  # For state-specific schemes
    is_active = Column(String(50), default="active")  # active, inactive, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    comparisons = relationship("SchemeComparison", back_populates="scheme")

    def __repr__(self):
        return f"<Scheme(scheme_id={self.scheme_id}, name={self.name})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "scheme_id": self.scheme_id,
            "name": self.name,
            "description": self.description,
            "benefits": self.benefits,
            "criteria": self.criteria,
            "advantages": self.advantages,
            "disadvantages": self.disadvantages,
            "required_documents": self.required_documents,
            "state": self.state,
        }


class SchemeComparison(Base):
    """
    ORM Model for Student-Scheme Eligibility Comparisons
    Stores eligibility check results and match scores
    """

    __tablename__ = "scheme_comparisons"

    # Primary Key
    comparison_id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Foreign Keys
    profile_id = Column(
        String(36),
        ForeignKey("student_profiles.profile_id"),
        nullable=False,
        index=True,
    )
    scheme_id = Column(
        String(100), ForeignKey("schemes.scheme_id"), nullable=False, index=True
    )

    # Eligibility Results
    match_score = Column(Float, nullable=False)  # 0.0 to 1.0
    is_eligible = Column(
        String(20), nullable=False
    )  # "Eligible", "Borderline", "Ineligible"

    # Detailed Results (stored as JSON)
    reasons = Column(JSON, nullable=False)  # List of matching reasons
    improvement_areas = Column(JSON, nullable=False)  # List of areas to improve

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    scheme = relationship("Scheme", back_populates="comparisons")

    def __repr__(self):
        return f"<SchemeComparison(profile_id={self.profile_id}, scheme_id={self.scheme_id}, match_score={self.match_score})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "comparison_id": self.comparison_id,
            "profile_id": self.profile_id,
            "scheme_id": self.scheme_id,
            "match_score": self.match_score,
            "is_eligible": self.is_eligible,
            "reasons": self.reasons,
            "improvement_areas": self.improvement_areas,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DecisionReport(Base):
    """
    ORM Model for Student Decision Reports
    Stores generated reports with action plans and recommendations
    """

    __tablename__ = "decision_reports"

    # Primary Key
    report_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key
    profile_id = Column(
        String(36),
        ForeignKey("student_profiles.profile_id"),
        nullable=False,
        index=True,
    )

    # Report Content (stored as JSON)
    executive_summary = Column(Text, nullable=False)
    eligible_schemes = Column(JSON, nullable=False)  # List of eligible scheme IDs
    borderline_schemes = Column(JSON, nullable=False)  # List of borderline scheme IDs
    ineligible_schemes = Column(JSON, nullable=False)  # List of ineligible scheme IDs

    # Action Plan and Timeline (stored as JSON)
    recommended_action_plan = Column(JSON, nullable=False)  # List of action steps
    next_steps = Column(JSON, nullable=False)  # List of timeline steps
    key_insights = Column(JSON, nullable=False)  # List of personalized insights

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<DecisionReport(report_id={self.report_id}, profile_id={self.profile_id})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "report_id": self.report_id,
            "profile_id": self.profile_id,
            "executive_summary": self.executive_summary,
            "eligible_schemes": self.eligible_schemes,
            "borderline_schemes": self.borderline_schemes,
            "ineligible_schemes": self.ineligible_schemes,
            "recommended_action_plan": self.recommended_action_plan,
            "next_steps": self.next_steps,
            "key_insights": self.key_insights,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

"""
DATABASE MODELS - SCHOLARAI GOVERNMENT SCHEMES PLATFORM
=======================================================

ORM Models: Python classes that map to database tables.
This version is designed for the ScholarAI government schemes discovery platform.

DATABASE SCHEMA:
- profiles: User information (name, age, income, state, goals)
- schemes: Government scheme data (name, category, eligibility, benefits)
- scheme_comparisons: Generated comparison reports (optional for MVP)

KEY CONCEPTS:
- Column: Database column definition
- UUID: Universal unique identifier (better than auto-incrementing integers for distributed systems)
- JSONB: JSON data in database (for flexible, nested data)
- Vector: AI embeddings for vector search (pgvector, Supabase)
- ForeignKey: Link between tables
- Relationship: Python representation of joins
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profile(Base):
    """
    Profile Model - represents user information

    Database table: profiles
    Stores user profile data for scheme matching and eligibility filtering.

    Fields:
    - id: UUID primary key (unique, distributed-system friendly)
    - name: User's full name
    - age: User's age (for age-based eligibility)
    - state: Indian state (for location-based scheme filtering)
    - income: Annual income in rupees (for income-based eligibility)
    - occupation: Job/occupation type (for occupation-based schemes)
    - education_level: Highest education completed (for education schemes)
    - category: Category (General, OBC, SC, ST - for reserved schemes)
    - goals: User's goals (e.g., "Education funding", "Healthcare")
    - created_at: When profile was created
    """

    __tablename__ = "profiles"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4,
        nullable=False,
    )

    # User Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Indexed for filtering
    income: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Annual income in rupees
    occupation: Mapped[str] = mapped_column(String(100), nullable=False)
    education_level: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # General, OBC, SC, ST
    goals: Mapped[str] = mapped_column(Text, nullable=False)  # User's goals/needs

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scheme_comparisons = relationship("SchemeComparison", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, name={self.name}, state={self.state})>"


class Scheme(Base):
    """
    Scheme Model - represents government scheme information

    Database table: schemes
    Stores information about government schemes that users can be matched to.

    Fields:
    - id: UUID primary key
    - scheme_name: Name of the government scheme
    - category: Scheme category (Education, Healthcare, Agriculture, etc.)
    - state: State(s) where scheme is applicable
    - description: Detailed description of the scheme
    - benefits: What benefits the scheme provides
    - eligibility: Eligibility criteria in text form
    - documents: Required documents (JSON array)
    - application_steps: Step-by-step application process (JSON array)
    - apply_url: URL to apply for the scheme
    - embedding: Vector representation for AI-based search (pgvector)
    - created_at: When scheme was added to database
    """

    __tablename__ = "schemes"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4,
        nullable=False,
    )

    # Scheme Information
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Multi-state schemes: comma-separated
    description: Mapped[str] = mapped_column(Text, nullable=False)
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured Data (JSON)
    documents: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # e.g., ["Aadhar", "Bank Account", "Income Certificate"]
    application_steps: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # Step-by-step guide

    # URL for application
    apply_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # AI/Vector Search
    # embedding: Vector for similarity search - will be added when using pgvector
    # For now, we store it as a JSON array for compatibility
    embedding: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # 1536-dimensional vector from OpenAI

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scheme_comparisons = relationship("SchemeComparison", back_populates="scheme")

    def __repr__(self) -> str:
        return f"<Scheme(id={self.id}, scheme_name={self.scheme_name}, category={self.category})>"


class SchemeComparison(Base):
    """
    SchemeComparison Model - stores generated comparison reports

    Database table: scheme_comparisons
    Stores the results of scheme comparisons and decision reports for audit/history.
    This is optional for MVP but useful for analytics and user history.

    Fields:
    - id: UUID primary key
    - profile_id: Reference to user profile
    - scheme_ids: List of scheme IDs compared (JSON array)
    - report: The generated comparison report (JSON)
    - created_at: When the comparison was generated
    """

    __tablename__ = "scheme_comparisons"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4,
        nullable=False,
    )

    # Foreign Keys
    profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True
    )

    # Data
    scheme_ids: Mapped[list] = mapped_column(
        JSONB, nullable=False
    )  # Array of scheme UUIDs compared
    report: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # Full comparison report

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    profile = relationship("Profile", back_populates="scheme_comparisons")

    def __repr__(self) -> str:
        return f"<SchemeComparison(id={self.id}, profile_id={self.profile_id})>"

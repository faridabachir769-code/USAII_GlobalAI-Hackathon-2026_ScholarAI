# app/db/database.py
# Database Configuration and Session Management
# Works with Supabase PostgreSQL

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Load environment variables
load_dotenv()

# ==================== DATABASE CONFIGURATION ====================

# For Supabase (PostgreSQL)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, construct it from Supabase credentials
if not DATABASE_URL:
    # Format: postgresql://user:password@host:port/database
    # Supabase provides connection string in Settings → Database → Connection string
    DATABASE_URL = "postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/[DATABASE]"


print(f"Database URL: {DATABASE_URL[:50]}...")  # Print only first part for security

# ==================== ENGINE CREATION ====================

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Check connections before using
    pool_size=10,
    max_overflow=20,
)

# ==================== SESSION FACTORY ====================

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ==================== DEPENDENCY INJECTION ====================


def get_db() -> Session:
    """
    Dependency for FastAPI endpoints to get database session

    Usage in FastAPI:
    @app.get("/students")
    def get_students(db: Session = Depends(get_db)):
        students = db.query(StudentProfile).all()
        return students
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== DATABASE INITIALIZATION ====================


def init_db():
    """
    Initialize database tables
    Call this once at startup to create all tables
    """
    from app.models.scheme import Base as SchemeBase
    from app.models.student import Base as StudentBase

    # Create all tables
    StudentBase.metadata.create_all(bind=engine)
    SchemeBase.metadata.create_all(bind=engine)

    print("✅ Database tables created successfully!")


# ==================== FOR ALEMBIC MIGRATIONS ====================

# Import models for Alembic to discover them
# Create base for migrations
from sqlalchemy.ext.declarative import declarative_base

from app.models.scheme import DecisionReport, Scheme, SchemeComparison
from app.models.student import StudentProfile

Base = declarative_base()

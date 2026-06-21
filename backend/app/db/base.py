"""
DATABASE MODULE - BASE
======================

This module sets up the database connection and session management.

KEY CONCEPTS:
- SQLAlchemy: ORM (Object-Relational Mapping) - maps Python classes to database tables
- Engine: Connection pool that manages database connections
- SessionLocal: Factory for creating database sessions
- Base: Parent class for all ORM models

DATABASE WORKFLOW:
1. Create engine → establish connection pool
2. Create SessionLocal → factory for sessions
3. Define models (inherit from Base)
4. Use sessions in endpoints to query/save data
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)

# SQLAlchemy Engine
# - Manages connection pool
# - Creates actual database connections
# - echo=True prints all SQL queries (for learning)
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    # Use StaticPool for SQLite testing, remove for production
    # poolclass=StaticPool if "sqlite" in settings.database_url else None,
)

# Session Factory
# - Creates new database sessions
# - A session is like a "workspace" for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
# - All your database models inherit from this
# - Used by Alembic migrations
Base = declarative_base()

log.info(f"Database connection configured: {settings.database_url}")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI endpoints.

    FastAPI Dependency Injection Pattern:
    - FastAPI calls this function automatically
    - Provides a fresh database session to each request
    - Closes session after request completes

    Usage in endpoint:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - creates all tables.

    Call this once when starting the application:
        from app.db.base import init_db
        init_db()

    This creates tables for all models that inherit from Base.
    """
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created/verified")

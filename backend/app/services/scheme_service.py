"""
SCHEME SERVICE - Business Logic for Government Schemes
======================================================

This service handles all database operations related to government schemes.
"""

from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.db.models import Scheme
from sqlalchemy.orm import Session

log = get_logger(__name__)


class SchemeService:
    @staticmethod
    def get_scheme(db: Session, scheme_id: UUID) -> Optional[Scheme]:
        """Retrieve a scheme by ID."""
        return db.query(Scheme).filter(Scheme.id == scheme_id).first()

    @staticmethod
    def list_schemes(db: Session, skip: int = 0, limit: int = 100) -> List[Scheme]:
        """List all schemes with pagination."""
        return db.query(Scheme).offset(skip).limit(limit).all()

    @staticmethod
    def count_schemes(db: Session) -> int:
        """Count total number of schemes."""
        return db.query(Scheme).count()

    @staticmethod
    def get_schemes_by_ids(db: Session, scheme_ids: List[UUID]) -> List[Scheme]:
        """Retrieve multiple schemes by their IDs."""
        return db.query(Scheme).filter(Scheme.id.in_(scheme_ids)).all()

    @staticmethod
    def get_schemes_by_state(db: Session, state: str) -> List[Scheme]:
        """Retrieve schemes available in a specific state."""
        # Using simple string match for now; could be improved with better state matching
        return db.query(Scheme).filter(Scheme.state.contains(state)).all()

"""
MAIN APPLICATION ENTRY POINT
============================

This is where everything comes together.

STARTUP SEQUENCE:
1. Create FastAPI app instance
2. Register routes (endpoints)
3. Initialize database
4. Start server

KEY CONCEPTS:
- FastAPI() creates the web server
- app.include_router() adds route groups
- lifespan() handles startup/shutdown events
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.comparison import router as comparison_router
from app.api.decision_report import router as decision_report_router
from app.api.eligibility import router as eligibility_router
from app.api.profiles import router as profiles_router
from app.core.config import settings
from app.core.logger import get_logger
from app.db.base import init_db

log = get_logger(__name__)


# ============== LIFESPAN EVENTS ==============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.

    Startup: Initialize database
    Shutdown: Cleanup resources
    """
    # STARTUP
    log.info("=== APPLICATION STARTUP ===")
    log.info(f"App: {settings.app_name} v{settings.app_version}")
    log.info(f"Database: {settings.database_url}")

    init_db()

    log.info("Application ready!")

    yield  # App runs while yielded

    # SHUTDOWN
    log.info("=== APPLICATION SHUTDOWN ===")
    log.info("Cleanup complete")


# ============== CREATE APP ==============

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ScholarAI Backend API for government schemes discovery and recommendation",
    lifespan=lifespan,  # Handle startup/shutdown
)

# ============== MIDDLEWARE ==============

# CORS: Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== INCLUDE ROUTERS ==============

# Add profile endpoints: /api/profile
app.include_router(profiles_router)

# Add eligibility endpoints: /api/eligibility
app.include_router(eligibility_router)

# Add comparison endpoints: /api/compare
app.include_router(comparison_router)

# Add decision report endpoints: /api/decision-report
app.include_router(decision_report_router)

# ============== ROOT ENDPOINT ==============


@app.get("/")
def root():
    """API root endpoint - basic health check."""
    return {
        "message": "ScholarAI Backend API",
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "app": settings.app_name}


# ============== ERROR HANDLERS ==============


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch any unhandled exceptions."""
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "detail": "Internal server error",
        "error_code": "INTERNAL_ERROR",
    }

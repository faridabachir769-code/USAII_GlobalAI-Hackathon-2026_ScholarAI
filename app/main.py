# app/main.py - UPDATED with compare routes
from fastapi import FastAPI

from app.api import compare, eligibility, profiles

app = FastAPI(
    title="ScholarAI",
    description="AI-powered tool to help students discover and apply for government schemes",
    version="0.1.0",
)

# Register routers
app.include_router(profiles.router)
app.include_router(eligibility.router)
app.include_router(compare.router)


@app.get("/")
async def root():
    return {
        "message": "ScholarAI API is running",
        "endpoints": [
            "GET  /docs (Swagger UI)",
            "GET  /redoc (ReDoc UI)",
            "POST /api/profile (create profile)",
            "GET  /api/profile/{profile_id} (get profile)",
            "POST /api/eligibility/check (check scheme eligibility)",
            "GET  /api/eligibility/schemes (list all schemes)",
            "POST /api/eligibility/bulk-check (check all schemes)",
            "POST /api/eligibility/test-data (create test profile)",
            "POST /api/compare/schemes (compare multiple schemes)",
            "POST /api/compare/decision-report (generate decision report)",
            "GET  /api/compare/report-template (get report template)",
        ],
    }

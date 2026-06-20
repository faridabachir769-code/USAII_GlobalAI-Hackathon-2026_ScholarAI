from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import profiles, eligibility, compare
from app.db.database import init_db

app = FastAPI(
    title="ScholarAI",
    description="AI-powered tool to help students discover government schemes",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"⚠️  DB initialization warning: {e}")

# Routers
app.include_router(profiles.router)
app.include_router(eligibility.router)
app.include_router(compare.router)

@app.get("/")
async def root():
    return {
        "message": "ScholarAI API is running",
        "database": "Connected to PostgreSQL via ORM",
        "docs": "Available at /docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

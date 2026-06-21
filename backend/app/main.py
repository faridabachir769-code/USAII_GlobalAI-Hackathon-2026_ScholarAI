import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.config import settings
from app.database import get_db, init_db, save_scheme_matches
from app.cache import get_profile, set_profile, get_history, set_history
from app.routes.integration import router as integration_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sahayak_backend")

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Sahayak AI Backend Gateway", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing Database...")
    init_db()
    logger.info("Database initialized successfully.")
    logger.info("Pre-loading embedding model...")
    try:
        from app.vector_store import _get_embedder
        _get_embedder()
        logger.info("Embedding model loaded.")
    except Exception as e:
        logger.warning(f"Could not pre-load embedding model: {e}")

class ChatRequest(BaseModel):
    query: str

class ProfileUpdate(BaseModel):
    student_required: Optional[bool] = None
    income_max: Optional[float] = None
    categories_allowed: Optional[str] = None
    states_allowed: Optional[str] = None
    gender_allowed: Optional[str] = None
    education_level: Optional[str] = None

def get_session_id(session_id: Optional[str] = Header(None)) -> str:
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Sahayak AI Backend Gateway v2"}

@app.get("/api/chat/history")
def get_chat_history(session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    chat_history = get_history(session_id, db=db)
    return {"session_id": session_id, "history": chat_history}

def fetch_profile(session_id: str, db: Optional[Session] = None) -> dict:
    profile = get_profile(session_id, db=db)
    if not profile:
        profile = {
            "student": False,
            "income": 10000000.0,
            "state": "National",
            "category": "General",
            "gender": "Any",
            "education": "Any",
            "disability": "None",
            "documents": {
                "aadhaar": False,
                "income_certificate": False
            }
        }
        set_profile(session_id, profile, db=db)
    return {"session_id": session_id, "profile": profile}


@app.post("/api/chat")
async def chat_handler(request: ChatRequest, session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    from app.agents.graph import workflow_run

    profile_response = fetch_profile(session_id, db=db)
    profile = profile_response["profile"]

    chat_history = get_history(session_id, db=db)
    chat_history.append({"role": "user", "content": request.query})

    start = datetime.utcnow()
    result = await workflow_run(request.query, profile, db, chat_history=chat_history)
    elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

    updated_profile = result.get("profile", profile)
    set_profile(session_id, updated_profile, db=db)

    response_text = result.get("response", "Could not generate response.")
    chat_history.append({"role": "assistant", "content": response_text})
    set_history(session_id, chat_history, db=db)

    # Enqueue LLM job to pgmq for analytics
    try:
        enqueue_llm_job("chat_completed", {
            "session_id": session_id,
            "query": request.query[:200],
            "response_time_ms": elapsed_ms,
            "schemes_found": len(result.get("matched_schemes", [])),
        }, priority=3)
    except Exception as e:
        logger.debug(f"Analytics enqueue skipped: {e}")

    # Persist matched schemes for the user (cached results)
    try:
        save_scheme_matches(session_id, result.get("matched_schemes", []), db)
    except Exception as e:
        logger.debug(f"Scheme match persistence skipped: {e}")

    return {
        "session_id": session_id,
        "response": response_text,
        "profile": updated_profile,
        "chat_history": chat_history,
        "matched_schemes": result.get("matched_schemes", []),
        "missing_fields": result.get("missing_fields", []),
        "youtube_videos": result.get("youtube_videos", []),
        "comparison_data": result.get("comparison_data", []),
        "decision_report": result.get("decision_report", {}),
        "action_plan": result.get("action_plan", []),
        "confidence": result.get("confidence", 50)
    }

@app.post("/api/document-upload")
async def document_upload(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    from app.services.doc_intelligence import extract_document_info

    logger.info(f"Received file upload: {file.filename} for session: {session_id}")

    contents = await file.read()

    extracted_data = await extract_document_info(contents, file.filename)

    profile_response = fetch_profile(session_id, db=db)
    profile = profile_response["profile"]

    if "income" in extracted_data and extracted_data["income"] is not None:
        profile["income"] = extracted_data["income"]
        profile["documents"]["income_certificate"] = True
    if "state" in extracted_data and extracted_data["state"] is not None:
        profile["state"] = extracted_data["state"]
    if "gender" in extracted_data and extracted_data["gender"] is not None:
        profile["gender"] = extracted_data["gender"]
    if "aadhaar" in file.filename.lower() or extracted_data.get("document_type") == "aadhaar":
        profile["documents"]["aadhaar"] = True

    set_profile(session_id, profile, db=db)

    return {
        "message": f"Successfully processed {file.filename}",
        "extracted_data": extracted_data,
        "profile": profile
    }

app.include_router(integration_router, prefix="/api")

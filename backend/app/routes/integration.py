import json
import logging
import base64
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db, Scheme, Rule, FAQ, Profile, ChatMessage, Feedback, SearchLog, UserSchemeMatch, save_scheme_matches
from app.cache import get_profile, set_profile, enqueue_llm_job
from app.vector_store import search_hybrid

logger = logging.getLogger(__name__)

router = APIRouter()


def extract_user_id(authorization: Optional[str] = Header(None)) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            parts = token.split(".")
            if len(parts) == 3:
                padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = base64.urlsafe_b64decode(padded)
                claims = json.loads(payload)
                return claims.get("sub", token[:20])
        except Exception:
            return token[:20]
    return "anonymous"


@router.get("/profile")
def get_user_profile(
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db),
):
    profile = get_profile(user_id, db=db)
    if not profile:
        profile = {
            "student": False,
            "income": 10000000.0,
            "state": "National",
            "category": "General",
            "gender": "Any",
            "education": "Any",
            "disability": "None",
            "documents": {"aadhaar": False, "income_certificate": False}
        }
        set_profile(user_id, profile, db=db)
    return {"id": user_id, **profile}


@router.post("/profile")
def create_profile(
    data: Dict[str, Any],
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db),
):
    profile = {
        "student": data.get("student", False),
        "income": float(data.get("annual_income", 10000000)),
        "state": data.get("state", "National"),
        "category": data.get("category", "General"),
        "gender": data.get("gender", "Any"),
        "education": data.get("education_level", "Any"),
        "disability": data.get("disability", "None"),
        "full_name": data.get("full_name", ""),
        "age": data.get("age", ""),
        "occupation": data.get("occupation", ""),
        "documents": {"aadhaar": False, "income_certificate": False}
    }
    set_profile(user_id, profile, db=db)
    persist_id = enqueue_llm_job("profile_updated", {"user_id": user_id, "profile": profile})
    return {"message": "Profile created", "profile": profile, "job_id": persist_id}


@router.put("/profile")
def update_profile(
    data: Dict[str, Any],
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db),
):
    existing = get_profile(user_id, db=db) or {}
    existing.update(data)
    if "annual_income" in data:
        existing["income"] = float(data["annual_income"])
    if "education_level" in data:
        existing["education"] = data["education_level"]
    set_profile(user_id, existing, db=db)
    return {"message": "Profile updated", "profile": existing}


def _scheme_to_dict(scheme: Scheme) -> dict:
    return {
        "id": scheme.id,
        "title": scheme.name,
        "description": scheme.description or "",
        "benefits": scheme.benefits or "",
        "eligibility_text": scheme.eligibility_text or "",
        "documents_required": scheme.documents_required or "",
        "application_process": scheme.application_process or "",
        "ministry": scheme.ministry or "",
        "application_link": scheme.application_link or "",
        "state": scheme.state or "National",
        "amount": scheme.benefits[:100] if scheme.benefits else None,
        "provider": scheme.ministry or None,
        "country": "India",
        "study_level": _infer_study_level(scheme),
        "deadline": None,
        "match_score": None,
        "source_url": scheme.application_link or None,
    }


def _infer_study_level(scheme: Scheme) -> str:
    text = (scheme.eligibility_text or "") + " " + (scheme.description or "")
    text_lower = text.lower()
    if any(w in text_lower for w in ["phd", "doctoral", "ph.d"]):
        return "PhD"
    if any(w in text_lower for w in ["postgraduate", "post graduate", "master", "pg"]):
        return "Postgraduate"
    if any(w in text_lower for w in ["engineering", "b.tech", "b.e"]):
        return "Engineering"
    if any(w in text_lower for w in ["graduate", "degree", "bachelor", "undergraduate", "ug"]):
        return "Undergraduate"
    if any(w in text_lower for w in ["diploma", "iti"]):
        return "Diploma"
    if any(w in text_lower for w in ["higher secondary", "12th", "11th", "hsc"]):
        return "Higher Secondary"
    if any(w in text_lower for w in ["school", "10th"]):
        return "School"
    return "All Levels"


@router.get("/schemes")
def list_schemes(
    search: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Scheme)
    if search:
        query = query.filter(Scheme.name.ilike(f"%{search}%"))
    if state:
        query = query.filter(Scheme.state.ilike(f"%{state}%"))
    if category:
        query = query.join(Rule).filter(Rule.categories_allowed.ilike(f"%{category}%"))
    total = query.count()
    schemes = query.order_by(Scheme.id).offset(offset).limit(limit).all()
    return {"schemes": [_scheme_to_dict(s) for s in schemes], "total": total}


@router.get("/schemes/recommended")
def recommended_schemes(
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db)
):
    profile = get_profile(user_id, db=db) or {}

    try:
        # Use the DB-side eligibility function from the migration
        rows = db.execute(sql_text("""
            SELECT * FROM get_eligible_schemes(
                p_income     := :income,
                p_category   := :category,
                p_state      := :state,
                p_gender     := :gender,
                p_education  := :education,
                p_disability := :disability,
                p_is_student := :is_student,
                p_limit      := 20
            )
        """), {
            "income": profile.get("income", 10000000),
            "category": profile.get("category", "General"),
            "state": profile.get("state", "National"),
            "gender": profile.get("gender", "Any"),
            "education": profile.get("education", "Any"),
            "disability": profile.get("disability", "None"),
            "is_student": profile.get("student", False),
        }).fetchall()

        results = []
        for row in rows:
            sd = {
                "id": row.id,
                "title": row.name,
                "description": row.description or "",
                "benefits": row.benefits or "",
                "eligibility_text": getattr(row, 'eligibility_text', None) or "",
                "documents_required": getattr(row, 'documents_required', None) or "",
                "application_process": getattr(row, 'application_process', None) or "",
                "ministry": row.ministry or None,
                "state": row.state or "National",
                "match_score": row.match_score,
                "match_reasons": row.match_reasons if isinstance(row.match_reasons, list) else [],
                "amount": (row.benefits or "")[:100] if row.benefits else None,
                "provider": row.ministry or None,
                "country": "India",
                "deadline": None,
                "source_url": getattr(row, 'application_link', None) or None,
                "study_level": "All Levels",
            }
            results.append(sd)
        return results
    except Exception as e:
        logger.warning(f"DB eligibility function failed, falling back to Python logic: {e}")
        db.rollback()

    # Fallback: Python-side eligibility
    schemes = db.query(Scheme).filter(Scheme.is_active == True).all()
    results = []
    for scheme in schemes:
        rules = db.query(Rule).filter(Rule.scheme_id == scheme.id).all()
        match_reasons = []
        for rule in rules:
            income = profile.get("income")
            if income is not None and rule.income_max and float(income) <= float(rule.income_max):
                match_reasons.append("Income eligible")
            if rule.categories_allowed:
                user_cat = (profile.get("category") or "").strip().lower()
                allowed = [c.strip().lower() for c in rule.categories_allowed.split(",")]
                if user_cat in allowed:
                    match_reasons.append("Category matches")
            if rule.states_allowed:
                user_state = (profile.get("state") or "").strip().lower()
                allowed = [s.strip().lower() for s in rule.states_allowed.split(",")]
                if user_state in allowed or "national" in allowed:
                    match_reasons.append("State matches")
            if rule.gender_allowed and rule.gender_allowed.lower() != "any":
                user_gender = (profile.get("gender") or "").strip().lower()
                if user_gender == rule.gender_allowed.lower():
                    match_reasons.append("Gender matches")

        # State guard: only known state/UT names are state-specific.
        # Ministry names in the state column are central — apply to all states.
        from app.agents.nodes import is_state_specific
        scheme_state = (scheme.state or "").strip().lower()
        user_state = (profile.get("state") or "").strip().lower()
        state_specific = is_state_specific(scheme_state)
        if (user_state and user_state != "national"
                and not is_central
                and scheme_state != user_state):
            continue

        score = min(95, 40 + len(match_reasons) * 10) if match_reasons else 20
        if match_reasons:
            sd = _scheme_to_dict(scheme)
            sd["match_score"] = score
            sd["match_reasons"] = match_reasons
            results.append(sd)
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:20]


@router.get("/schemes/{scheme_id}")
def get_scheme(scheme_id: int, db: Session = Depends(get_db)):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    sd = _scheme_to_dict(scheme)
    rules = db.query(Rule).filter(Rule.scheme_id == scheme.id).all()
    faqs = db.query(FAQ).filter(FAQ.scheme_id == scheme.id).all()
    sd["rules"] = [
        {
            "student_required": r.student_required,
            "income_max": float(r.income_max) if r.income_max else None,
            "categories_allowed": r.categories_allowed,
            "states_allowed": r.states_allowed,
            "gender_allowed": r.gender_allowed,
            "education_level": r.education_level,
        }
        for r in rules
    ]
    sd["faqs"] = [{"question": f.question, "answer": f.answer} for f in faqs]
    return sd


class CompareRequest(BaseModel):
    scheme_ids: List[int]


@router.post("/schemes/compare")
def compare_schemes(
    req: CompareRequest,
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db)
):
    profile = get_profile(user_id) or {}
    schemes = db.query(Scheme).filter(Scheme.id.in_(req.scheme_ids)).all()
    results = []
    for scheme in schemes:
        rules = db.query(Rule).filter(Rule.scheme_id == scheme.id).all()
        match_reasons = []
        for rule in rules:
            income = profile.get("income")
            if income is not None and rule.income_max and float(income) <= float(rule.income_max):
                match_reasons.append("Income eligible")
            if rule.categories_allowed:
                user_cat = (profile.get("category") or "").strip().lower()
                allowed = [c.strip().lower() for c in rule.categories_allowed.split(",")]
                if user_cat in allowed:
                    match_reasons.append("Category matches")
            if rule.states_allowed:
                user_state = (profile.get("state") or "").strip().lower()
                allowed = [s.strip().lower() for s in rule.states_allowed.split(",")]
                if user_state in allowed or "national" in allowed:
                    match_reasons.append("State matches")
        sd = _scheme_to_dict(scheme)
        sd["match_reasons"] = match_reasons
        sd["eligibility_difficulty"] = "Easy" if len(match_reasons) >= 3 else "Medium" if match_reasons else "Hard"
        sd["approval_likelihood"] = "High" if len(match_reasons) >= 3 else "Medium" if match_reasons else "Low"
        results.append(sd)
    return {"comparison": results}


class SimulateRequest(BaseModel):
    scheme_id: int
    annual_income: Optional[float] = None
    education_level: Optional[str] = None
    category: Optional[str] = None
    age: Optional[int] = None


@router.post("/schemes/simulate")
def simulate_scheme(
    req: SimulateRequest,
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.id == req.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    profile = get_profile(user_id) or {}
    sim_profile = dict(profile)
    if req.annual_income is not None:
        sim_profile["income"] = req.annual_income
    if req.education_level:
        sim_profile["education"] = req.education_level
    if req.category:
        sim_profile["category"] = req.category

    rules = db.query(Rule).filter(Rule.scheme_id == scheme.id).all()
    match_count = 0
    total_checks = 0
    details = []
    for rule in rules:
        if rule.income_max:
            total_checks += 1
            income = sim_profile.get("income")
            if income is not None and float(income) <= float(rule.income_max):
                match_count += 1
                details.append(f"Income ₹{float(income):,.0f} ≤ limit ₹{float(rule.income_max):,.0f}")
            else:
                details.append(f"Income exceeds limit of ₹{float(rule.income_max):,.0f}")
        if rule.categories_allowed:
            total_checks += 1
            user_cat = (sim_profile.get("category") or "").strip().lower()
            allowed = [c.strip().lower() for c in rule.categories_allowed.split(",")]
            if user_cat in allowed:
                match_count += 1
                details.append(f"Category '{user_cat}' is allowed")
            else:
                details.append(f"Category '{user_cat}' not in allowed list")
        if rule.states_allowed:
            total_checks += 1
            user_state = (sim_profile.get("state") or "").strip().lower()
            allowed = [s.strip().lower() for s in rule.states_allowed.split(",")]
            if user_state in allowed or "national" in allowed:
                match_count += 1
                details.append(f"State '{user_state}' is covered")
            else:
                details.append(f"State '{user_state}' not in allowed areas")

    score = int((match_count / max(total_checks, 1)) * 100)
    return {
        "match_score": score,
        "explanation": "; ".join(details[:5]),
        "recommendation": "You may qualify" if score >= 50 else "May not qualify based on simulated profile",
    }


class DecisionReportRequest(BaseModel):
    scheme_id: int
    user_query: Optional[str] = ""


@router.post("/decision-report")
def generate_decision_report(
    req: DecisionReportRequest,
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db)
):
    scheme = db.query(Scheme).filter(Scheme.id == req.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    profile = get_profile(user_id) or {}
    sd = _scheme_to_dict(scheme)

    rules = db.query(Rule).filter(Rule.scheme_id == scheme.id).all()
    match_reasons = []
    for rule in rules:
        income = profile.get("income")
        if income is not None and rule.income_max and float(income) <= float(rule.income_max):
            match_reasons.append("Income eligibility met")
        if rule.categories_allowed:
            user_cat = (profile.get("category") or "").strip().lower()
            allowed = [c.strip().lower() for c in rule.categories_allowed.split(",")]
            if user_cat in allowed:
                match_reasons.append("Category matches")
        if rule.states_allowed:
            user_state = (profile.get("state") or "").strip().lower()
            allowed = [s.strip().lower() for s in rule.states_allowed.split(",")]
            if user_state in allowed or "national" in allowed:
                match_reasons.append("State coverage matches")
        if rule.gender_allowed and rule.gender_allowed.lower() != "any":
            user_gender = (profile.get("gender") or "").strip().lower()
            if user_gender == rule.gender_allowed.lower():
                match_reasons.append("Gender criteria met")

    score = min(95, 40 + len(match_reasons) * 10) if match_reasons else 20
    analysis = f"You meet {len(match_reasons)} out of several eligibility criteria." if match_reasons else "Your profile partially matches the general criteria."

    sd["match_score"] = score
    sd["match_reasons"] = match_reasons

    return {
        "scheme": sd,
        "eligibility_analysis": analysis,
        "expected_benefits": sd.get("benefits", "Financial support as per scheme guidelines."),
        "risks": "Double-check deadlines, required documents, and specific eligibility conditions before applying." if score < 60 else "Low risk based on current profile match.",
        "final_recommendation": "This scheme is a strong match — we recommend applying." if score >= 60 else "Consider reviewing eligibility criteria or exploring alternative schemes.",
        "match_score": score,
    }


# ── New: Hybrid search endpoint ───────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    min_score: float = 0.3


@router.post("/schemes/search")
def search_schemes(
    req: SearchRequest,
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db)
):
    start = datetime.utcnow()
    results = search_hybrid(db, req.query, limit=req.limit, min_score=req.min_score)
    elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

    # Log search for analytics
    try:
        log_entry = SearchLog(
            query_text=req.query,
            user_id=user_id if user_id != "anonymous" else None,
            result_count=len(results),
            response_time=elapsed,
            filters={},
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Search log failed: {e}")

    return {
        "query": req.query,
        "results": results,
        "count": len(results),
        "time_ms": elapsed,
    }


# ── New: User feedback ────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    scheme_id: int
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    interaction_type: Optional[str] = None


@router.post("/feedback")
def submit_feedback(
    req: FeedbackRequest,
    user_id: str = Depends(extract_user_id),
    db: Session = Depends(get_db)
):
    fb = Feedback(
        user_id=user_id if user_id != "anonymous" else None,
        scheme_id=req.scheme_id,
        rating=req.rating,
        feedback_text=req.feedback_text,
        interaction_type=req.interaction_type,
    )
    db.add(fb)
    db.commit()
    return {"message": "Feedback recorded", "id": fb.id}


# ── New: pg_net webhook receiver ──────────────────────────────────────────

class WebhookPayload(BaseModel):
    scheme_id: int
    scheme_name: str
    timestamp: str


@router.post("/webhooks/scheme-match")
async def scheme_match_webhook(payload: WebhookPayload):
    """Receives notifications from pg_net when new schemes are added."""
    logger.info(f"Webhook received: new scheme '{payload.scheme_name}' (id={payload.scheme_id})")
    return {"status": "received"}


# ── New: pgmq job status ──────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    from app.database import LLMJob
    from uuid import UUID
    try:
        job = db.query(LLMJob).filter(LLMJob.id == UUID(job_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")


# ── New: GraphQL proxy (falls back to REST if pg_graphql not available) ────

@router.post("/graphql")
async def graphql_proxy(request: Request, db: Session = Depends(get_db)):
    """Proxy to Supabase pg_graphql endpoint."""
    try:
        body = await request.json()
        from app.config import settings
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.SUPABASE_URL}/graphql/v1",
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "apikey": settings.SUPABASE_KEY or "",
                },
                timeout=30
            )
            return resp.json()
    except Exception as e:
        logger.warning(f"GraphQL proxy failed: {e}")
        raise HTTPException(status_code=502, detail="GraphQL proxy unavailable")

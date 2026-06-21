import re
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, Boolean, ForeignKey, Float, JSON, DateTime, BigInteger, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pgvector.sqlalchemy import Vector
from app.config import settings

logger = logging.getLogger(__name__)

engine_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
elif "postgresql" in settings.DATABASE_URL or "supabase" in settings.DATABASE_URL:
    engine_args["pool_pre_ping"] = True
    engine_args["pool_size"] = 10

engine = create_engine(settings.DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── Existing models (enhanced) ────────────────────────────────────────────

# ── Existing models (enhanced) ────────────────────────────────────────────

class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    benefits = Column(Text, nullable=False)
    eligibility_text = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    application_process = Column(Text, nullable=True)
    documents_required = Column(Text, nullable=True)
    sources_and_references = Column(Text, nullable=True)
    ministry = Column(String(255), nullable=True)
    application_link = Column(String(500), nullable=True)
    state = Column(String(100), default="National")
    scraped_at = Column(String(50), nullable=True)
    extra_data = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)

    rules = relationship("Rule", back_populates="scheme", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="scheme", cascade="all, delete-orphan")
    embeddings = relationship("SchemeEmbedding", back_populates="scheme", cascade="all, delete-orphan")

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"))
    student_required = Column(Boolean, default=False)
    income_max = Column(Numeric(precision=12, scale=2), default=10000000.0)
    categories_allowed = Column(String(255), nullable=True)
    states_allowed = Column(String(255), nullable=True)
    gender_allowed = Column(String(50), default="Any")
    education_level = Column(String(100), default="Any")

    scheme = relationship("Scheme", back_populates="rules")

class FAQ(Base):
    __tablename__ = "faq"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    scheme = relationship("Scheme", back_populates="faqs")

class SchemeEmbedding(Base):
    __tablename__ = "scheme_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, default=0)
    section = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scheme = relationship("Scheme", back_populates="embeddings")

# ── New unified models ────────────────────────────────────────────────────

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    profile_data = Column(JSONB, default={})
    preferences = Column(JSONB, default={})
    is_onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    context_data = Column(JSONB, default={})
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class LLMJob(Base):
    __tablename__ = "llm_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    priority = Column(Integer, default=5)
    payload = Column(JSONB, nullable=False)
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchLog(Base):
    __tablename__ = "search_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    user_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    result_count = Column(Integer, default=0)
    vector_score = Column(Float, nullable=True)
    trigram_score = Column(Float, nullable=True)
    response_time = Column(Integer, nullable=True)
    filters = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"))
    rating = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    interaction_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSchemeMatch(Base):
    __tablename__ = "user_scheme_matches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Integer, default=0)
    match_reasons = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    refreshed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "scheme_id", name="uq_user_scheme"),
    )

# ── User-Scheme Match persistence ─────────────────────────────────────────

def save_scheme_matches(user_id: str, matched_schemes: list, db):
    """Upsert matched schemes for a user — used to cache pipeline results."""
    if not user_id or user_id in ("", "anonymous"):
        return
    from datetime import datetime
    now = datetime.utcnow()
    for ms in matched_schemes:
        existing = db.query(UserSchemeMatch).filter(
            UserSchemeMatch.user_id == user_id,
            UserSchemeMatch.scheme_id == ms["id"],
        ).first()
        if existing:
            existing.match_score = ms.get("match_score", 50)
            existing.match_reasons = ms.get("match_reasons", [])
            existing.is_active = True
            existing.refreshed_at = now
        else:
            db.add(UserSchemeMatch(
                user_id=user_id,
                scheme_id=ms["id"],
                match_score=ms.get("match_score", 50),
                match_reasons=ms.get("match_reasons", []),
                is_active=True,
                refreshed_at=now,
            ))
    db.commit()

def get_user_scheme_matches(user_id: str, db, limit: int = 20) -> list:
    """Get cached scheme matches for a user."""
    if not user_id or user_id in ("", "anonymous"):
        return []
    rows = db.query(UserSchemeMatch).filter(
        UserSchemeMatch.user_id == user_id,
        UserSchemeMatch.is_active == True,
    ).order_by(UserSchemeMatch.match_score.desc()).limit(limit).all()
    return [{
        "user_id": r.user_id,
        "scheme_id": r.scheme_id,
        "match_score": r.match_score,
        "match_reasons": r.match_reasons,
        "refreshed_at": r.refreshed_at.isoformat() if r.refreshed_at else None,
    } for r in rows]

# ── Dependency ────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def parse_eligibility_heuristic(eligibility_text: str) -> dict:
    rules = {}
    if not eligibility_text:
        return rules

    text = eligibility_text.lower()

    def parse_indian_number(s: str) -> float:
        digits = [c for c in s if c.isdigit() or c == ","]
        s_clean = "".join(digits)
        if not s_clean:
            return 0.0
        if "," not in s_clean:
            return float(s_clean)
        parts = s_clean.split(",")
        if len(parts) >= 2 and len(parts[-1]) == 3:
            last = parts.pop()
            return float("".join(parts) + last)
        cleaned = s_clean.replace(",", "")
        return float(cleaned) if cleaned else 0.0

    lakh_or_k_patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs)",
        r"(\d+(?:\.\d+)?)\s*(?:thousand|k)",
        r"(?:rs\.?|inr|rupees)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|per annum|annually)",
    ]
    for pat in lakh_or_k_patterns:
        m = re.search(pat, text)
        if m and m.group(1):
            val = float(m.group(1))
            if val == 0:
                continue
            if "lakh" in pat:
                val *= 100000
            elif "thousand" in pat or pat == r"(\d+(?:\.\d+)?)\s*(?:thousand|k)":
                val *= 1000
            if 0 < val < 10000000:
                rules["income_max"] = val
                break

    if "income_max" not in rules:
        income_patterns = [
            r"annual income[:\s]*[₹rs.\s]*([\d,]+(?:\.\d+)?)",
            r"income[:\s]*[₹rs.\s]*([\d,]+(?:\.\d+)?)",
            r"(?:less than|below|under|upto|up to|not exceeding|maximum)[\s]*[₹rs.\s]*([\d,]+(?:\.\d+)?)",
        ]
        for pat in income_patterns:
            m = re.search(pat, text)
            if m:
                val = parse_indian_number(m.group(1))
                if 0 < val < 10000000:
                    rules["income_max"] = val
                    break

    students_keywords = [
        "student", "students", "studying", "school", "schools", "college", 
        "colleges", "pursuing", "class", "classes", "course", "courses", 
        "admission", "admissions"
    ]
    if any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in students_keywords):
        rules["student_required"] = True

    cat_map = {
        "sc": "SC", "st": "ST", "obc": "OBC", "ebc": "EBC",
        "dnt": "DNT", "general": "General", "scheduled caste": "SC",
        "scheduled tribe": "ST", "other backward": "OBC",
        "economically backward": "EBC", "denotified": "DNT",
        "s.c.": "SC", "s.t.": "ST", "o.b.c.": "OBC", "e.b.c.": "EBC",
        "obc-ncl": "OBC",
    }
    found_cats = []
    # Split text into sentences and filter out concession/relaxation lines to avoid false categorization
    sentences = re.split(r'\. |\n', text)
    filtered_sentences = []
    for s in sentences:
        s_lower = s.lower()
        if not any(w in s_lower for w in ["relaxation", "concession", "reservation", "preference", "prefer", "quota"]):
            filtered_sentences.append(s)
    
    category_text = " ".join(filtered_sentences)
    
    for key, val in cat_map.items():
        if re.search(r'\b' + re.escape(key) + r'\b', category_text):
            found_cats.append(val)
    if found_cats:
        rules["categories_allowed"] = ",".join(sorted(set(found_cats)))

    state_keywords = [
        "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
        "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand",
        "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
        "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
        "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
        "uttar pradesh", "uttarakhand", "west bengal", "delhi",
        "jammu and kashmir", "jammu & kashmir", "ladakh", "chandigarh",
        "puducherry", "lakshadweep", "national"
    ]
    found_states = []
    for s in state_keywords:
        if re.search(r'\b' + re.escape(s) + r'\b', text):
            found_states.append(s.title())
    if found_states:
        rules["states_allowed"] = ",".join(sorted(set(found_states)))

    gender_keywords_female = ["female", "girl", "girls", "women", "woman", "daughter", "daughters"]
    gender_keywords_male = ["male", "boy", "boys", "son", "sons"]
    
    if any(re.search(r'\b' + re.escape(w) + r'\b', text) for w in gender_keywords_female):
        rules["gender_allowed"] = "Female"
    elif any(re.search(r'\b' + re.escape(w) + r'\b', text) for w in gender_keywords_male):
        rules["gender_allowed"] = "Male"

    edu_map = [
        ("phd", "PhD"), ("ph.d", "PhD"), ("doctoral", "PhD"),
        ("post graduate", "Postgraduate"), ("postgraduate", "Postgraduate"), ("pg", "Postgraduate"),
        ("diploma", "Diploma"), ("iti", "Diploma"),
        ("undergraduate", "Graduate"), ("under graduate", "Graduate"), ("ug", "Graduate"),
        ("graduate", "Graduate"), ("degree", "Graduate"), ("bachelor", "Graduate"),
        ("engineering", "Engineering"), ("b.tech", "Engineering"), ("b.e", "Engineering"), ("b.e.", "Engineering"),
        ("higher secondary", "HigherSecondary"), ("12th", "HigherSecondary"), ("intermediate", "HigherSecondary"),
        ("school", "School"), ("10th", "School"), ("class", "School"),
    ]
    for key, val in edu_map:
        pattern = r'\b' + re.escape(key) + r'\b'
        if key.endswith('.'):
            pattern = r'\b' + re.escape(key)
        
        if re.search(pattern, text):
            rules["education_level"] = val
            break

    return rules

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Scheme).count() == 0:
            yasasvi = Scheme(
                name="PM YASASVI",
                benefits="Scholarship of up to ₹1,25,000 per year for OBC, EBC and DNT students studying in Class 9 to 12 or Top Class Colleges.",
                ministry="Ministry of Social Justice and Empowerment",
                application_link="https://yet.nta.ac.in/",
                state="National"
            )
            db.add(yasasvi)
            db.commit()
            db.refresh(yasasvi)

            db.add(Rule(
                scheme_id=yasasvi.id,
                student_required=True,
                income_max=250000.0,
                categories_allowed="OBC,EBC,DNT",
                states_allowed="National",
                gender_allowed="Any",
                education_level="Engineering"
            ))
            db.add(FAQ(
                scheme_id=yasasvi.id,
                question="How do I apply for PM YASASVI?",
                answer="You can apply online through the NTA YASASVI portal or National Scholarship Portal (NSP) when applications open."
            ))

            pudhumai = Scheme(
                name="Pudhumai Penn Scheme",
                benefits="Financial assistance of ₹1,000 per month for girls who studied in government schools from classes 6 to 12 and are pursuing higher education.",
                ministry="Social Welfare and Women Empowerment Department, Tamil Nadu",
                application_link="https://penkalvi.tn.gov.in/",
                state="Tamil Nadu"
            )
            db.add(pudhumai)
            db.commit()
            db.refresh(pudhumai)

            db.add(Rule(
                scheme_id=pudhumai.id,
                student_required=True,
                income_max=500000.0,
                categories_allowed="SC,ST,OBC,General",
                states_allowed="Tamil Nadu",
                gender_allowed="Female",
                education_level="Graduate"
            ))
            db.add(FAQ(
                scheme_id=pudhumai.id,
                question="Who is eligible for Pudhumai Penn Scheme?",
                answer="Girls who studied in government schools in Tamil Nadu from classes 6 to 12 and are enrolled in a college degree, diploma, or ITI course are eligible."
            ))

            db.commit()
            logger.info("Database initialized and seeded.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
    finally:
        db.close()

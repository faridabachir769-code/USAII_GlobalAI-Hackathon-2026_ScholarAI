import re
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Scheme, Rule, FAQ
from app.vector_store import search_similar_documents, get_embedding
from app.services.youtube_service import get_tutorial_videos
from app.agents.state import AgentState
from app.agents.schemas import ProfileExtraction, ComparisonItem, DecisionReport, ActionPlanItem, IncomeVerificationResult, SearchQueryRewrite, DISABILITY_OPTIONS
from app.services.ai_service import generate_structured_json, generate_text

logger = logging.getLogger(__name__)

STATE_NAMES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Dadra & Nagar Haveli and Daman & Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]
_STATE_NAMES_LOWER = [s.lower() for s in STATE_NAMES]

def is_state_specific(state_value: str) -> bool:
    """True if the scheme's state field is a known Indian state/UT name,
    meaning it should only be shown to residents of that state.
    False for ministry names, 'National', NULL, or other non-state values."""
    if not state_value:
        return False
    return state_value.strip().lower() in _STATE_NAMES_LOWER

CATEGORIES = ["SC", "ST", "OBC", "EBC", "DNT", "General"]
EDUCATION_LEVELS = ["School", "HigherSecondary", "Diploma", "Graduate", "Postgraduate", "Engineering", "PhD", "Any"]

_EDUCATION_SEM_CACHE = {}

def education_semantic_match(user_edu: Optional[str], rule_edu: Optional[str]) -> bool:
    if not user_edu or not rule_edu:
        return True
    u = user_edu.strip().lower()
    r = rule_edu.strip().lower()
    if r == "any":
        return True
    if u == r:
        return True
    KNOWN_MAP = {
        "10th": "school", "ssc": "school", "matric": "school", "class 10": "school",
        "12th": "highersecondary", "hsc": "highersecondary", "intermediate": "highersecondary", "class 12": "highersecondary",
        "b.tech": "engineering", "b.e": "engineering", "bachelor of technology": "engineering", "be": "engineering",
        "b.sc": "graduate", "b.a": "graduate", "b.com": "graduate", "bachelor": "graduate", "bachelor's": "graduate",
        "m.sc": "postgraduate", "m.a": "postgraduate", "m.com": "postgraduate", "master": "postgraduate", "master's": "postgraduate",
        "m.tech": "postgraduate", "m.e": "postgraduate", "ph.d": "phd", "phd": "phd", "doctoral": "phd",
        "iti": "diploma", "polytechnic": "diploma",
    }
    mapped_u = KNOWN_MAP.get(u, u)
    mapped_r = KNOWN_MAP.get(r, r)
    if mapped_u == mapped_r:
        return True
    cache_key = f"{mapped_u}|{mapped_r}"
    if cache_key in _EDUCATION_SEM_CACHE:
        return _EDUCATION_SEM_CACHE[cache_key]
    try:
        import numpy as np
        u_emb = np.array(get_embedding(mapped_u, is_query=False))
        r_emb = np.array(get_embedding(mapped_r, is_query=False))
        sim = float(np.dot(u_emb, r_emb) / (np.linalg.norm(u_emb) * np.linalg.norm(r_emb)))
        result = sim >= 0.55
        _EDUCATION_SEM_CACHE[cache_key] = result
        if not result:
            logger.debug(f"Education semantic mismatch: '{user_edu}' vs '{rule_edu}' (sim={sim:.3f})")
        return result
    except Exception as e:
        logger.warning(f"Education semantic match failed, using exact: {e}")
        return u == r

async def context_agent(state: AgentState) -> Dict[str, Any]:
    query = state.get("user_query", "")
    current_profile = state.get("profile", {})
    chat_history = state.get("chat_history", [])

    q = query.lower()

    # Build conversation context from recent history (last 4 exchanges)
    recent_history = chat_history[-8:] if chat_history else []
    conversation_context = ""
    if recent_history:
        conv_lines = []
        for msg in recent_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            conv_lines.append(f"{role}: {msg.get('content', '')}")
        conversation_context = "## Previous Conversation\n" + "\n\n".join(conv_lines) + "\n\n"

    # --- Intent Detection (scoring-based) ---
    # Browse signals weighted by specificity
    browse_score = 0
    for phrase in ["list all", "all schemes in", "all schemes of", "browse schemes"]:
        browse_score += (3 if phrase in q else 0)
    for phrase in ["list", "show me", "tell me about", "what are", "what is",
                   "schemes in", "schemes for", "schemes of", "all schemes",
                   "browse", "filter", "find schemes", "search schemes",
                   "which schemes", "name some", "give me", "available in",
                   "available for", "can i get", "what schemes", "any schemes",
                   "is there", "are there", "schemes available"]:
        browse_score += (1 if phrase in q else 0)

    personal_score = 0
    for phrase in ["i am", "i'm", "my income", "my family", "i study",
                   "i earn", "i belong", "i live in", "i come from",
                   "i am from", "i'm from", "i need", "i want to apply",
                   "am i eligible", "can i get", "will i get",
                   "suggest", "recommend", "best scheme", "which scheme",
                   "what should", "help me choose", "top scheme"]:
        personal_score += (2 if phrase in q else 0)
    for phrase in ["my", "i have", "i am a", "i'm a"]:
        personal_score += (1 if phrase in q else 0)

    # If previous chat context exists and user had set personal details,
    # a short follow-up ("what about me?", "tell me more") should be personal
    has_filled_profile = (
        current_profile.get("state") not in ("", "National")
        or current_profile.get("income", 10000000) < 10000000
    )
    if has_filled_profile and len(q.split()) <= 5:
        personal_score += 2

    # Strong profile-based signals: user has profile AND asks for suggestions
    if has_filled_profile and any(w in q for w in ["suggest", "recommend", "best", "help me", "which one"]):
        personal_score += 3

    intent = "browse" if browse_score >= personal_score else "personalize"

    extracted_profile = {}

    if intent == "browse":
        # --- Browse mode: extract filters (state, category, gender, education, income) ---
        for state_name in STATE_NAMES:
            if re.search(r'\b' + re.escape(state_name.lower()) + r'\b', q):
                extracted_profile["state"] = state_name
                break
        for cat in CATEGORIES:
            if re.search(r'\b' + re.escape(cat.lower()) + r'\b', q):
                extracted_profile["category"] = cat
                break
        if any(w in q for w in ["female", "girl", "woman", "women"]):
            extracted_profile["gender"] = "Female"
        elif any(w in q for w in ["male", "boy", "man"]):
            extracted_profile["gender"] = "Male"
        if any(w in q for w in ["student", "studying", "college", "school", "pursuing", "class", "course"]):
            extracted_profile["student"] = True
        if any(w in q for w in ["blind", "visually impaired"]):
            extracted_profile["disability"] = "Blind"
        elif any(w in q for w in ["hearing", "deaf"]):
            extracted_profile["disability"] = "Hearing Impaired"
        # Education level extraction for browse queries
        for edu in EDUCATION_LEVELS:
            if edu.lower() in q:
                extracted_profile["education"] = edu
                break
        if not extracted_profile.get("education"):
            if any(w in q for w in ["engineering", "b.tech", "b.e", "bachelor of technology"]):
                extracted_profile["education"] = "Engineering"
            elif any(w in q for w in ["graduate", "degree", "bachelor", "b.sc", "b.a", "b.com"]):
                extracted_profile["education"] = "Graduate"
            elif any(w in q for w in ["postgraduate", "master", "m.sc", "m.a", "m.com", "m.tech", "phd", "ph.d"]):
                extracted_profile["education"] = "Postgraduate"
            elif any(w in q for w in ["school", "10th", "12th", "ssc", "hsc", "higher secondary"]):
                extracted_profile["education"] = "HigherSecondary"
        # Income extraction for browse queries (e.g., "schemes for income below 2.5 lakh")
        income_match = re.search(r"(?:income|earning|salary|below|less than|under)\s*(?:of\s*)?(\d+)\s*(lakh|l|thousand|k)?", q)
        if not income_match:
            income_match = re.search(r"(\d+)\s*(lakh|l|thousand|k)?\s*(?:income|earnings|salary|p\.?a\.?)?", q)
        if income_match:
            try:
                num = int(income_match.group(1))
                unit = (income_match.group(2) or "").lower()
                if unit in ("lakh", "l"):
                    num *= 100000
                elif unit in ("thousand", "k"):
                    num *= 1000
                if 0 < num < 10000000:
                    extracted_profile["income"] = num
            except ValueError:
                pass

        extracted_profile = {k: v for k, v in extracted_profile.items() if v is not None}
        merged_profile = {**current_profile, **extracted_profile}
        return {"profile": merged_profile, "intent": "browse"}

    # --- Personalize mode (existing logic) ---
    # Adaptive: skip LLM extraction if profile already has meaningful values
    has_meaningful_profile = (
        current_profile.get("state", "") not in ("", "National")
        and current_profile.get("income", 10000000) < 10000000
        and current_profile.get("category", "") not in ("", "General")
        and current_profile.get("education", "") not in ("", "Any")
    )

    needs_llm = settings.LOCAL_LLM_URL and not has_meaningful_profile

    if needs_llm:
        try:
            # Adaptive: shorter prompt when some profile fields already exist
            filled_count = sum(1 for k in ("state", "income", "category", "education", "gender", "disability") if current_profile.get(k) not in (None, "", "Any", "National", "None"))
            if filled_count >= 3:
                prompt = (
                    f"{conversation_context}"
                    f"Extract any NEW demographic fields from this query that are not already in the profile. "
                    f"Existing profile: {json.dumps(current_profile)}\n"
                    f"Current query: \"{query}\"\n\n"
                    f"Only extract fields explicitly mentioned. Return null for unmentioned fields."
                )
            else:
                prompt = (
                    f"You are an Indian government welfare scheme profile extraction expert.\n\n"
                    f"{conversation_context}"
                    f"## Task\n"
                    f"Analyze the user's query (and previous conversation context) and extract their demographic and eligibility profile. "
                    f"Merge extracted values with the existing profile state — new values override old ones.\n\n"
                    f"## Input\n"
                    f"- Current Profile State: {json.dumps(current_profile)}\n"
                    f"- User Query: \"{query}\"\n\n"
                    f"## Extraction Rules\n"
                    f"1. Extract ONLY values that are explicitly stated or clearly implied in the query.\n"
                    f"2. For income: convert to annual INR. Handle formats like '2 lakh', '2.5l', '250000', '2.5 LPA'.\n"
                    f"3. For state: use full state name (e.g., 'Tamil Nadu', 'Maharashtra').\n"
                    f"4. For category: normalize to standard codes: SC, ST, OBC, EBC, DNT, General.\n"
                    f"5. For education: map to these levels: School, HigherSecondary, Diploma, "
                    f"Graduate, Postgraduate, Engineering, PhD.\n"
                    f"6. For disability: use the exact format: None, Blind, Hearing Impaired, "
                    f"Physically Handicapped, Mentally Challenged, Multiple Disabilities.\n"
                    f"   Use 'None' if no disability is mentioned.\n"
                    f"7. If a field is not mentioned, set it to null (do not guess).\n\n"
                    f"## Output Schema Field Reference\n"
                    f"- `student` (boolean): true if user says they study/are a student\n"
                    f"- `income` (number): annual family income in INR\n"
                    f"- `state` (string): Indian state name\n"
                    f"- `category` (string): social category code [SC, ST, OBC, EBC, DNT, General]\n"
                    f"- `gender` (string): Male, Female, or Other\n"
                    f"- `education` (string): education level\n"
                    f"- `disability` (string): disability status [None, Blind, Hearing Impaired, "
                    f"Physically Handicapped, Mentally Challenged, Multiple Disabilities]"
                )
            extracted_profile = await generate_structured_json(prompt, ProfileExtraction)
            logger.info(f"AI Service Context extracted: {extracted_profile}")
        except Exception as e:
            logger.error(f"AI Service Context extraction failed: {e}. Using regex extractor fallback.")

    # Always run regex/cue-based extraction for fields the LLM didn't fill,
    # so partial LLM extraction doesn't prevent filling missing fields.
    if not extracted_profile.get("student") and any(w in query.lower() for w in ["student", "studying", "college", "school", "pursuing", "class", "course"]):
        extracted_profile["student"] = True

    if not extracted_profile.get("income"):
        income_match = re.search(r"(\d+)\s*(lakh|l|thousand|k)?\s*(income|earn|rupees|rs|per annum|annually)?", query.lower())
        if income_match:
            try:
                num = int(income_match.group(1))
                unit = (income_match.group(2) or "").lower()
                if unit in ("lakh", "l"):
                    num = num * 100000
                elif unit in ("thousand", "k"):
                    num = num * 1000
                if num < 10000000:
                    extracted_profile["income"] = num
            except ValueError:
                pass

    if not extracted_profile.get("state"):
        for state_name in STATE_NAMES:
            if re.search(r'\b' + re.escape(state_name.lower()) + r'\b', query.lower()):
                extracted_profile["state"] = state_name
                break

    if not extracted_profile.get("category"):
        for cat in CATEGORIES:
            if re.search(r'\b' + re.escape(cat.lower()) + r'\b', query.lower()):
                extracted_profile["category"] = cat
                break

    if not extracted_profile.get("gender"):
        if "female" in query.lower() or "girl" in query.lower() or "daughter" in query.lower() or "woman" in query.lower():
            extracted_profile["gender"] = "Female"
        elif "male" in query.lower() or "boy" in query.lower() or "son" in query.lower():
            extracted_profile["gender"] = "Male"

    if not extracted_profile.get("education"):
        for edu in EDUCATION_LEVELS:
            if edu.lower() in query.lower():
                extracted_profile["education"] = edu
                break
        if not extracted_profile.get("education"):
            if any(w in query.lower() for w in ["engineering", "b.tech", "b.e", "bachelor of technology"]):
                extracted_profile["education"] = "Engineering"
            elif any(w in query.lower() for w in ["graduate", "degree", "bachelor", "b.sc", "b.a", "b.com"]):
                extracted_profile["education"] = "Graduate"
            elif any(w in query.lower() for w in ["postgraduate", "master", "m.sc", "m.a", "m.com", "m.tech", "phd", "ph.d"]):
                extracted_profile["education"] = "Postgraduate"
            elif any(w in query.lower() for w in ["school", "10th", "12th", "ssc", "hsc", "higher secondary"]):
                extracted_profile["education"] = "HigherSecondary"

    if not extracted_profile.get("disability"):
        query_lower = query.lower()
        if any(w in query_lower for w in ["blind", "visually impaired", "vision"]):
            extracted_profile["disability"] = "Blind"
        elif any(w in query_lower for w in ["hearing", "deaf", "hearing impaired"]):
            extracted_profile["disability"] = "Hearing Impaired"
        elif any(w in query_lower for w in ["physically handicapped", "orthopedic", "physically challenged", "mobility"]):
            extracted_profile["disability"] = "Physically Handicapped"
        elif any(w in query_lower for w in ["mentally challenged", "intellectual disability", "mental retardation"]):
            extracted_profile["disability"] = "Mentally Challenged"
        elif any(w in query_lower for w in ["multiple disability", "multiple disabilities"]):
            extracted_profile["disability"] = "Multiple Disabilities"
        elif any(w in query_lower for w in ["disabled", "disability", "handicapped", "divyang"]):
            extracted_profile["disability"] = "Physically Handicapped"

    extracted_profile = {k: v for k, v in extracted_profile.items() if v is not None}

    merged_profile = {**current_profile, **extracted_profile}

    return {"profile": merged_profile}


async def question_planner(state: AgentState) -> Dict[str, Any]:
    profile = state.get("profile", {})
    intent = state.get("intent", "personalize")
    missing_fields = []

    # In browse mode, don't ask for personal details — only state/category filters
    if intent == "browse":
        if not profile.get("state"):
            missing_fields.append("state")
        if not profile.get("category"):
            missing_fields.append("category")
        return {"missing_fields": missing_fields}

    if profile.get("student") is None:
        missing_fields.append("student")
    if profile.get("income") is None or profile.get("income") == 10000000.0:
        missing_fields.append("income")
    if not profile.get("state"):
        missing_fields.append("state")
    if not profile.get("category"):
        missing_fields.append("category")
    if not profile.get("gender"):
        missing_fields.append("gender")
    if not profile.get("education"):
        missing_fields.append("education")
    if not profile.get("disability") or profile.get("disability") in ("", None):
        missing_fields.append("disability")

    return {"missing_fields": missing_fields}


async def eligibility_agent(state: AgentState) -> Dict[str, Any]:
    db: Session = state.get("db_session")
    profile = state.get("profile", {})
    intent = state.get("intent", "personalize")

    if not db:
        logger.error("No database session available for Eligibility Agent.")
        return {"matched_schemes": []}

    schemes = db.query(Scheme).all()
    matched_schemes = []
    user_cat = profile.get("category", "").strip().lower()
    user_state = profile.get("state", "").strip().lower()

    for scheme in schemes:
        rules = db.query(Rule).filter(Rule.scheme_id == scheme.id).all()
        if not rules:
            matched_schemes.append({
                "id": scheme.id,
                "name": scheme.name,
                "benefits": scheme.benefits,
                "description": scheme.description or "",
                "eligibility_text": scheme.eligibility_text or "",
                "documents_required": scheme.documents_required or "",
                "application_process": scheme.application_process or "",
                "ministry": scheme.ministry,
                "application_link": scheme.application_link,
                "state": scheme.state
            })
            continue

        # --- Browse mode: relaxed filtering ---
        if intent == "browse":
            passes_browse = True
            browse_reasons = []
            for rule in rules:
                if rule.states_allowed and user_state:
                    allowed = [s.strip().lower() for s in rule.states_allowed.split(",")]
                    if user_state not in allowed and "national" not in allowed:
                        passes_browse = False
                        break
                if rule.categories_allowed and user_cat:
                    allowed = [c.strip().lower() for c in rule.categories_allowed.split(",")]
                    general_only = len(allowed) == 1 and allowed[0] == "general"
                    if not general_only and user_cat not in allowed:
                        passes_browse = False
                        break
            if not passes_browse:
                continue
            # Scheme-level state guard: scheme.state may be a state name or a ministry name.
            # Only known state/UT names are treated as state-specific.
            s_state = (scheme.state or "").strip().lower()
            state_specific = is_state_specific(s_state)
            if user_state and user_state != "national" and state_specific and s_state != user_state:
                continue
            if user_cat:
                browse_reasons.append(f"Category '{profile.get('category')}' filter")
            if user_state:
                browse_reasons.append(f"State '{profile.get('state')}' filter")
            matched_schemes.append({
                "id": scheme.id,
                "name": scheme.name,
                "benefits": scheme.benefits,
                "description": scheme.description or "",
                "eligibility_text": scheme.eligibility_text or "",
                "documents_required": scheme.documents_required or "",
                "application_process": scheme.application_process or "",
                "ministry": scheme.ministry,
                "application_link": scheme.application_link,
                "state": scheme.state,
                "match_reasons": browse_reasons
            })
            continue

        # --- Personalize mode: full rules matching ---
        is_eligible = True
        match_reasons = []

        for rule in rules:
            if rule.student_required and not profile.get("student", False):
                is_eligible = False
                break

            user_income = profile.get("income")
            if user_income is not None and user_income > float(rule.income_max):
                is_eligible = False
                break
            elif user_income is not None:
                match_reasons.append(f"Income ₹{user_income:,.0f} ≤ ₹{float(rule.income_max):,.0f} limit")

            if rule.categories_allowed:
                allowed_cats = [c.strip().lower() for c in rule.categories_allowed.split(",")]
                user_cat = profile.get("category", "").strip().lower()
                if user_cat:
                    is_general_only = len(allowed_cats) == 1 and allowed_cats[0] == "general"
                    if is_general_only:
                        match_reasons.append("Category 'General' (open to all)")
                    elif user_cat not in allowed_cats:
                        is_eligible = False
                        break
                    else:
                        match_reasons.append(f"Category '{profile.get('category')}' matches")

            if rule.states_allowed:
                allowed_states = [s.strip().lower() for s in rule.states_allowed.split(",")]
                user_state = profile.get("state", "").strip().lower()
                if user_state and user_state not in allowed_states and "national" not in allowed_states:
                    is_eligible = False
                    break
                elif user_state:
                    match_reasons.append(f"State '{profile.get('state')}' matches")

            if rule.gender_allowed and rule.gender_allowed.lower() != "any":
                user_gender = profile.get("gender", "").strip().lower()
                if user_gender and user_gender not in ("", "any") and user_gender != rule.gender_allowed.lower():
                    is_eligible = False
                    break
                elif user_gender and user_gender not in ("", "any"):
                    match_reasons.append(f"Gender matches")

            if rule.education_level and rule.education_level.lower() != "any":
                user_edu = profile.get("education", "").strip().lower()
                if user_edu and user_edu not in ("", "any"):
                    if not education_semantic_match(user_edu, rule.education_level.lower()):
                        is_eligible = False
                        break
                    match_reasons.append(f"Education '{profile.get('education')}' matches")

            # Disability check — look in raw eligibility_text for disability keywords
            user_disability = profile.get("disability", "").strip().lower()
            if user_disability and user_disability != "none":
                el_text_lower = (scheme.eligibility_text or "").lower()
                disability_keywords = {
                    "blind": ["blind", "visually impaired", "vision", "visual impairment"],
                    "hearing impaired": ["hearing", "deaf", "hearing impaired", "auditory"],
                    "physically handicapped": ["physically handicapped", "physically challenged", "orthopedic", "mobility", "locomotor"],
                    "mentally challenged": ["mentally challenged", "intellectual disability", "mental retardation", "mentally retarded"],
                    "multiple disabilities": ["multiple disability", "multiple disabilities"],
                }
                keywords = disability_keywords.get(user_disability, [])
                if keywords and any(kw in el_text_lower for kw in keywords):
                    match_reasons.append(f"Disability '{profile.get('disability')}' matches scheme criteria")
                elif keywords and not any(kw in el_text_lower for kw in keywords):
                    # If the scheme doesn't mention this disability, still eligible (not a blocker)
                    pass

        # Scheme-level state guard: scheme.state may be a state name or a ministry name.
        # Only known state/UT names are treated as state-specific and restricted.
        if is_eligible:
            user_state_val = profile.get("state", "").strip().lower()
            scheme_state_val = (scheme.state or "").strip().lower()
            state_specific = is_state_specific(scheme_state_val)
            if state_specific:
                # State-specific scheme — user must match
                if (user_state_val and user_state_val != "national"
                        and scheme_state_val != user_state_val):
                    is_eligible = False
                    logger.info(f"State guard excluded {scheme.name}: "
                                f"user={user_state_val}, scheme={scheme_state_val}")

        if is_eligible:
            matched_schemes.append({
                "id": scheme.id,
                "name": scheme.name,
                "benefits": scheme.benefits,
                "description": scheme.description or "",
                "eligibility_text": scheme.eligibility_text or "",
                "documents_required": scheme.documents_required or "",
                "application_process": scheme.application_process or "",
                "ministry": scheme.ministry,
                "application_link": scheme.application_link,
                "state": scheme.state,
                "match_reasons": match_reasons
            })

    return {"matched_schemes": matched_schemes}


async def llm_income_verifier(state: AgentState) -> Dict[str, Any]:
    matched_schemes = state.get("matched_schemes", [])
    profile = state.get("profile", {})
    user_income = profile.get("income")

    if not matched_schemes or user_income is None:
        return {"matched_schemes": matched_schemes}

    if not settings.LOCAL_LLM_URL:
        return {"matched_schemes": matched_schemes}

    # Adaptive: skip LLM for 1-2 schemes (deterministic rule already covers them)
    if len(matched_schemes) <= 2:
        return {"matched_schemes": matched_schemes}

    # Adaptive: adjust eligibility text length based on scheme count
    el_text_limit = 300 if len(matched_schemes) > 8 else 500
    schemes_text = []
    for i, ms in enumerate(matched_schemes):
        el_text = (ms.get("eligibility_text", "") or "")[:el_text_limit]
        schemes_text.append(f"[{i}] {ms['name']}: {el_text[:80]}...")

    # Adaptive: shorter prompt when income is very high (most schemes qualify)
    high_income = user_income >= 5000000
    prompt = (
        f"Verify income eligibility for user earning ₹{user_income:,.0f}.\n\n"
        f"## Rules\n"
        f"1. Read each scheme's eligibility text for income limits.\n"
        f"2. No limit mentioned → qualifies by income.\n"
        f"3. Income ≤ limit → qualifies.\n"
        f"4. Output qualifying scheme zero-based indices.\n\n"
        + ("Most schemes likely qualify (high income).\n" if high_income else "")
        + "\n".join(schemes_text)
        + "\n\nOutput JSON: {\"qualifying_indices\": [0, 2, ...]}"
    )

    try:
        result = await generate_structured_json(prompt, IncomeVerificationResult)
        qualifying = set(result.get("qualifying_indices", []))
        if qualifying:
            filtered = [ms for i, ms in enumerate(matched_schemes) if i in qualifying]
            logger.info(
                f"LLM income verifier: {len(matched_schemes)} → {len(filtered)} schemes "
                f"(removed {len(matched_schemes) - len(filtered)} by income criteria)"
            )
            return {"matched_schemes": filtered}
    except Exception as e:
        logger.error(f"LLM income verifier failed: {e}. Using deterministic results as-is.")

    return {"matched_schemes": matched_schemes}


async def retrieval_agent(state: AgentState) -> Dict[str, Any]:
    db: Session = state.get("db_session")
    matched_schemes = state.get("matched_schemes", [])
    profile = state.get("profile", {})
    user_query = state.get("user_query", "")

    retrieved_docs = []
    youtube_videos = []

    # Build maps of scheme names and states from DB for resolution of search results
    scheme_name_map = {}
    scheme_state_map = {}
    scheme_ministry_map = {}
    matched_scheme_names = {}
    if db:
        try:
            all_schemes = db.query(Scheme).all()
            for s in all_schemes:
                scheme_name_map[s.id] = s.name
                scheme_state_map[s.id] = s.state or ""
                scheme_ministry_map[s.id] = s.ministry or ""
            for ms in matched_schemes:
                matched_scheme_names[ms["id"]] = ms["name"]
        except Exception as e:
            logger.error(f"Failed to load schemes for name resolution: {e}")

    # Batch load FAQs for all matched schemes (single query instead of N queries)
    if db and matched_schemes:
        try:
            matched_ids_list = [ms["id"] for ms in matched_schemes]
            faq_batch = db.query(FAQ).filter(FAQ.scheme_id.in_(matched_ids_list)).all()
            for faq in faq_batch:
                scheme_name = matched_scheme_names.get(faq.scheme_id, f"Scheme #{faq.scheme_id}")
                retrieved_docs.append({
                    "scheme_name": scheme_name,
                    "scheme_id": faq.scheme_id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "type": "faq"
                })
        except Exception as e:
            logger.error(f"Batch FAQ loading failed: {e}")

    # Vector search: rewrite user query into a search-optimized query via LLM (structured JSON)
    search_query = user_query
    retry_count = state.get("retry_count", 0)
    try:
        if settings.LOCAL_LLM_URL and retry_count == 0:
            income_str = f"₹{profile.get('income'):,.0f}" if profile.get("income") else "any income"
            profile_summary = ", ".join(
                f"{k}: {v}" for k, v in profile.items()
                if v is not None and v != "" and k != "documents"
            )
            rewrite_prompt = (
                f"You are a search query optimizer for an Indian government welfare scheme "
                f"vector database.\n\n"
                f"## Task\n"
                f"Rewrite the citizen's question into a concise, keyword-dense search query "
                f"that will retrieve the most relevant scheme documents from a vector database.\n\n"
                f"## Strategy\n"
                f"1. Extract key entities from the user profile and question:\n"
                f"   - Demographic: category (OBC/SC/ST/General), state, gender, age\n"
                f"   - Financial: income amount (e.g., '2.5 lakh', '₹250000')\n"
                f"   - Educational: student status, education level (School/Graduate/etc.)\n"
                f"   - Scheme type: keywords like 'scholarship', 'subsidy', 'pension', 'loan', "
                f"'assistance', 'fellowship', 'startup'\n"
                f"2. Combine these into a natural-sounding but keyword-rich phrase.\n"
                f"3. The query will be matched against document chunks with titles like "
                f"'eligibility for SchemeName', 'benefits for SchemeName', 'FAQs about SchemeName'.\n\n"
                f"## Input\n"
                f"- User profile: {profile_summary}\n"
                f"- User income: {income_str}\n"
                f"- Original question: \"{user_query}\"\n\n"
                f"## Output\n"
                f"`search_query` (string): concise keyword-rich search query (10-50 words). "
                f"Must include income amount if available, category, state, education level, "
                f"and benefit type keywords."
            )
            rewritten = await generate_structured_json(rewrite_prompt, SearchQueryRewrite)
            rq = rewritten.get("search_query", "").strip().strip('"').strip("'")
            if len(rq) > 5 and len(rq) < 500:
                generic_queries = {"string", "search query", "keywords", "government scheme", ""}
                if rq.lower() in generic_queries or len(rq.split()) < 2:
                    logger.warning(f"Query rewrite produced generic output, using original: '{rq}'")
                else:
                    search_query = rq
                    logger.info(f"Query rewritten: \"{user_query[:50]}...\" → \"{search_query[:80]}...\"")
        elif retry_count > 0:
            # Adaptive: on retry, use broader query with more welfare keywords
            search_query = f"{user_query} government scheme financial assistance scholarship benefits eligibility India"
            logger.info(f"Retry {retry_count}: using broadened query: \"{search_query[:80]}...\"")
    except Exception as e:
        logger.warning(f"Query rewrite failed, using original: {e}")

    try:
        matched_ids = [s["id"] for s in matched_schemes] if matched_schemes else None
        # Search documents filtered by matched scheme IDs for speed and precision
        vec_results = search_similar_documents(
            search_query,
            db=db,
            limit=settings.RETRIEVAL_VEC_SEARCH_LIMIT,
            threshold=settings.VECTOR_SEARCH_THRESHOLD,
            scheme_ids=matched_ids
        )

        # Group by scheme, boost National, apply MMR diversity selection
        by_scheme = {}
        for r in vec_results:
            sid = r.get("payload", {}).get("scheme_id")
            if not sid:
                continue
            if sid not in by_scheme:
                by_scheme[sid] = []
            by_scheme[sid].append(r)

        def _mmr_select(results, query_emb, lambda_param=None, max_results=None):
            if lambda_param is None:
                lambda_param = settings.MMR_LAMBDA
            if max_results is None:
                max_results = settings.RETRIEVAL_MAX_CHUNKS_PER_SCHEME
            """Maximal Marginal Relevance selection for diverse chunks."""
            if not results:
                return []
            selected = []
            candidate_scores = []
            for r in results:
                text = r.get("text", "")
                # Use the existing relevance score from vector search
                relevance = r.get("score", 0.0)
                candidate_scores.append({"result": r, "relevance": relevance, "text": text, "selected": False})
            
            while len(selected) < max_results and len(selected) < len(candidate_scores):
                best_idx = -1
                best_score = -float("inf")
                for i, c in enumerate(candidate_scores):
                    if c["selected"]:
                        continue
                    # Diversity penalty: max similarity to already selected
                    diversity_penalty = 0.0
                    if selected:
                        max_sim = max(
                            _text_similarity(c["text"], s["text"])
                            for s in selected
                        )
                        diversity_penalty = max_sim
                    mmr_score = lambda_param * c["relevance"] - (1 - lambda_param) * diversity_penalty
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = i
                if best_idx >= 0:
                    candidate_scores[best_idx]["selected"] = True
                    selected.append(candidate_scores[best_idx])
            return [s["result"] for s in selected]

        def _text_similarity(t1, t2):
            """Rough text similarity based on word overlap (fast, no model needed)."""
            if not t1 or not t2:
                return 0.0
            w1 = set(t1.lower().split())
            w2 = set(t2.lower().split())
            if not w1 or not w2:
                return 0.0
            return len(w1 & w2) / max(len(w1 | w2), 1)

        user_state = profile.get("state", "").strip().lower()
        for sid, results in by_scheme.items():
            scheme_name = scheme_name_map.get(sid, f"Scheme #{sid}")
            scheme_state = (scheme_state_map.get(sid, "") or "").strip()
            is_national = "national" in (scheme_state).lower()

            # State guard: only known state/UT names are state-specific.
            # Ministry names in the state column are central schemes — apply to all.
            state_specific = is_state_specific(scheme_state)
            if user_state and user_state != "national" and state_specific:
                if scheme_state.lower() != user_state:
                    logger.info(f"Retrieval state guard skipped {scheme_name}: "
                                f"user={user_state}, scheme_state={scheme_state}")
                    continue

            # Select diverse chunks using MMR
            diverse_results = _mmr_select(results, None, lambda_param=0.5, max_results=6)
            for r in diverse_results:
                section = r.get("payload", {}).get("section", "")
                retrieved_docs.append({
                    "scheme_name": scheme_name,
                    "scheme_id": sid,
                    "question": section,
                    "answer": r.get("text", ""),
                    "is_national": is_national,
                    "type": "embedding_chunk"
                })

        logger.info(f"Retrieval Agent: {len(vec_results)} vector results → {len(retrieved_docs)} docs")
    except Exception as e:
        logger.error(f"Vector search failed in Retrieval Agent: {e}")

    # YouTube search for top matched schemes
    for ms in matched_schemes[:3]:
        try:
            videos = get_tutorial_videos(ms["name"], profile.get("state", "National"))
            youtube_videos.extend(videos)
        except Exception as e:
            logger.error(f"YouTube search failed in Retrieval Agent: {e}")

    return {
        "retrieved_docs": retrieved_docs,
        "youtube_videos": youtube_videos
    }


async def relevance_verifier(state: AgentState) -> Dict[str, Any]:
    retrieved_docs = state.get("retrieved_docs", [])
    retry_count = state.get("retry_count", 0)
    user_query = state.get("user_query", "")
    profile = state.get("profile", {})
    matched_schemes = state.get("matched_schemes", [])

    if not matched_schemes:
        return {"confidence": 10, "retry_count": 0}

    # Step 1: Score-based relevance check (fast path)
    avg_score = 0.0
    if retrieved_docs:
        avg_score = sum(d.get("relevance_score", 0) or d.get("score", 0) for d in retrieved_docs) / max(len(retrieved_docs), 1)

    query_words = set(w for w in user_query.lower().split() if len(w) > 3)
    has_scheme_keyword = True
    if query_words:
        has_scheme_keyword = any(
            any(w in (ms.get("name", "") or "").lower()
                or w in (ms.get("benefits", "") or "").lower()
                for w in query_words)
            for ms in matched_schemes[:10]
        )

    # Step 2: LLM verification — verify matched schemes against actual profile
    if settings.LOCAL_LLM_URL and matched_schemes:
        try:
            schemes_snippet = []
            for ms in matched_schemes[:5]:
                schemes_snippet.append({
                    "name": ms["name"],
                    "state": ms.get("state", ""),
                    "ministry": ms.get("ministry", ""),
                    "eligibility": ms.get("eligibility_text", "")[:300],
                    "benefits": ms.get("benefits", "")[:200],
                    "match_reasons": ms.get("match_reasons", [])
                })

            verify_prompt = f"""You are an eligibility verification expert for Indian government schemes.

User Profile: {json.dumps(profile)}

Matched Schemes:
{json.dumps(schemes_snippet, indent=2)}

For each scheme, verify whether the user's profile ACTUALLY matches the scheme's eligibility rules based on the provided eligibility text, state, and category requirements.

Output a JSON object with:
- "verified_scheme_indices": list of zero-based indices that are genuinely good matches
- "explanation": brief reasoning for any schemes that were excluded

Base your analysis STRICTLY on the provided data — do not guess."""
            verify_result = await generate_structured_json(verify_prompt, type("VerificationResult", (), {
                "model_json_schema": classmethod(lambda cls: {
                    "type": "object",
                    "properties": {
                        "verified_scheme_indices": {"type": "array", "items": {"type": "integer"}},
                        "explanation": {"type": "string"}
                    },
                    "required": ["verified_scheme_indices", "explanation"]
                }),
                "model_validate_json": classmethod(lambda cls, data: json.loads(data))
            }))
            verified_indices = verify_result.get("verified_scheme_indices", [])
            if verified_indices:
                matched_schemes = [matched_schemes[i] for i in verified_indices if i < len(matched_schemes)]
                logger.info(f"LLM verification: kept {len(matched_schemes)}/{len(verified_indices)} verified schemes")
        except Exception as e:
            logger.warning(f"LLM verification failed, using all matched schemes: {e}")

    relevance_ok = avg_score >= settings.RELEVANCE_THRESHOLD or has_scheme_keyword
    if relevance_ok or retry_count >= settings.MAX_RETRIES:
        confidence = min(95, int(50 + avg_score * 50)) if retrieved_docs else 60
        return {"confidence": confidence, "retry_count": 0, "matched_schemes": matched_schemes}

    retry_count += 1
    expanded_query = f"{user_query} scholarship financial assistance government scheme benefits eligibility India"
    return {
        "user_query": expanded_query,
        "retry_count": retry_count,
    }


async def comparison_agent(state: AgentState) -> Dict[str, Any]:
    matched_schemes = state.get("matched_schemes", [])
    profile = state.get("profile", {})

    if not matched_schemes:
        return {"comparison_data": []}

    if len(matched_schemes) == 1:
        ms = matched_schemes[0]
        return {
            "comparison_data": [{
                "scheme_name": ms["name"],
                "financial_benefit": ms["benefits"][:200],
                "eligibility_difficulty": "Medium",
                "required_documents_count": 5,
                "processing_time": "4-6 weeks",
                "approval_likelihood": "High" if len(ms.get("match_reasons", [])) > 2 else "Medium",
                "renewal_required": True,
                "goal_alignment": "Based on your profile, this scheme appears well-aligned.",
                "notes": "This is the only scheme you match. We recommend proceeding with the application."
            }]
        }

    # Adaptive: for 2 schemes, deterministic comparison (no LLM needed)
    if len(matched_schemes) == 2 and not settings.LOCAL_LLM_URL:
        comparison_data = []
        for ms in matched_schemes:
            reasons = ms.get("match_reasons", [])
            comparison_data.append({
                "scheme_name": ms["name"],
                "financial_benefit": ms["benefits"][:200],
                "eligibility_difficulty": "Easy" if len(reasons) >= 3 else "Medium" if reasons else "Hard",
                "required_documents_count": 5,
                "processing_time": "4-6 weeks",
                "approval_likelihood": "High" if len(reasons) >= 3 else "Medium" if reasons else "Low",
                "renewal_required": True,
                "goal_alignment": f"Matches {len(reasons)} eligibility criteria",
                "notes": ms.get("ministry", "") or ""
            })
        return {"comparison_data": comparison_data}

    if settings.LOCAL_LLM_URL:
        try:
            schemes_summary = [{
                "name": m["name"],
                "benefits": m.get("benefits", ""),
                "eligibility_text": m.get("eligibility_text", "")[:500],
                "description": m.get("description", "")[:300],
                "documents_required": (m.get("documents_required", "") or "")[:200],
                "application_process": (m.get("application_process", "") or "")[:200],
                "state": m["state"],
                "ministry": m["ministry"],
                "match_reasons": m.get("match_reasons", [])
            } for m in matched_schemes]

            prompt = f"""You are a government scheme comparison expert. Compare these schemes using ONLY the provided data — do not guess or fabricate information.

User Profile: {json.dumps(profile)}

Schemes to compare:
{json.dumps(schemes_summary, indent=2)}

For each scheme, analyze the actual eligibility text and benefits to determine:
- financial_benefit: extract specific amounts from benefits field
- eligibility_difficulty: based on actual eligibility rules complexity
- required_documents_count: count from documents_required field
- processing_time: extract from application_process if mentioned
- approval_likelihood: based on how well profile matches the actual eligibility rules
- goal_alignment: explain how this scheme fits the user's specific situation
- notes: include any relevant details from the eligibility_text

Return a JSON array. Base ALL fields on the provided data."""
            comparison_raw = await generate_structured_json(prompt, type("ComparisonList", (), {
                "model_json_schema": classmethod(lambda cls: {
                    "type": "array",
                    "items": ComparisonItem.model_json_schema()
                }),
                "model_validate_json": classmethod(lambda cls, data: json.loads(data))
            }))
            if isinstance(comparison_raw, list):
                return {"comparison_data": comparison_raw}
        except Exception as e:
            logger.error(f"AI comparison failed: {e}")

    comparison_data = []
    for ms in matched_schemes:
        reasons = ms.get("match_reasons", [])
        comparison_data.append({
            "scheme_name": ms["name"],
            "financial_benefit": ms["benefits"][:200],
            "eligibility_difficulty": "Easy" if len(reasons) >= 3 else "Medium" if reasons else "Hard",
            "required_documents_count": 5,
            "processing_time": "4-6 weeks",
            "approval_likelihood": "High" if len(reasons) >= 3 else "Medium" if reasons else "Low",
            "renewal_required": True,
            "goal_alignment": f"Matches {len(reasons)} eligibility criteria",
            "notes": ms.get("ministry", "") or ""
        })

    return {"comparison_data": comparison_data}


async def decision_advisor(state: AgentState) -> Dict[str, Any]:
    matched_schemes = state.get("matched_schemes", [])
    comparison_data = state.get("comparison_data", [])
    retrieved_docs = state.get("retrieved_docs", [])
    profile = state.get("profile", {})
    chat_history = state.get("chat_history", [])
    recent_history = chat_history[-6:] if chat_history else []
    conversation_context = ""
    if recent_history:
        conv_lines = []
        for msg in recent_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            conv_lines.append(f"{role}: {msg.get('content', '')}")
        conversation_context = "## Previous Conversation\n" + "\n\n".join(conv_lines) + "\n\n"

    if not matched_schemes:
        response_text = ("Based on our eligibility analysis, you do not appear to match any of our currently indexed schemes.\n\n"
                         "**Suggestions:**\n"
                         "• Double-check your profile details (income, state, category, etc.)\n"
                         "• Upload your Income Certificate or Aadhaar for document-based verification\n"
                         "• You may qualify for state-specific schemes not yet indexed")
        return {"response": response_text, "decision_report": {}, "action_plan": []}

    # --- Browse mode: clean list response with breakdown ---
    intent = state.get("intent", "personalize")
    if intent == "browse":
        lines = []
        p = state.get("profile", {})

        # Breakdown stats
        state_count = len([s for s in matched_schemes if s.get("state", "").lower() not in ("", "national")])
        central_count = len([s for s in matched_schemes if s.get("state", "").lower() in ("", "national")])
        ministries = {}
        for s in matched_schemes:
            m = s.get("ministry", "Unknown").strip()
            ministries[m] = ministries.get(m, 0) + 1
        top_mins = sorted(ministries.items(), key=lambda x: -x[1])[:3]

        filters_parts = []
        if p.get("state"):
            filters_parts.append(f"**{p['state']}**")
        if p.get("category"):
            filters_parts.append(f"**{p['category']}** category")
        if p.get("education"):
            filters_parts.append(f"**{p['education']}** education")
        if p.get("gender"):
            filters_parts.append(f"**{p['gender']}**")
        if p.get("income") and p["income"] < 10000000:
            filters_parts.append(f"income under **₹{p['income']:,.0f}**")

        filter_text = " + ".join(filters_parts) if filters_parts else "all available"

        user_state = p.get("state", "")
        state_line = f" — Since you are a resident of **{user_state}**, state-specific schemes for {user_state} are shown alongside central schemes." if user_state and user_state != "National" else ""

        lines.append(f"🔍 Found **{len(matched_schemes)}** scheme(s) matching {filter_text}.{state_line}\n")

        if state_count > 0 and central_count > 0:
            lines.append(f"📊 **Breakdown:** {state_count} state-level, {central_count} central schemes")
        elif state_count > 0:
            lines.append(f"📊 **Breakdown:** {state_count} state-level schemes")
        elif central_count > 0:
            lines.append(f"📊 **Breakdown:** {central_count} central schemes")
        if top_mins:
            lines.append(f"🏛  **Top ministries:** {', '.join(f'{m}({c})' for m, c in top_mins)}")
        lines.append("")

        for i, ms in enumerate(matched_schemes[:25], 1):
            tag = "🇮🇳 Central" if ms.get("state", "").lower() in ("", "national") else f"🏛 {ms.get('state', 'State')}"
            lines.append(f"**{i}. {ms['name']}**  `{tag}`")
            benefit = ms.get('benefits', '')
            if benefit:
                lines.append(f"   💰 {benefit[:150]}")
            if ms.get("match_reasons"):
                lines.append(f"   ✓ {'; '.join(ms['match_reasons'])}")
            if ms.get("ministry"):
                lines.append(f"   🏢 {ms['ministry']}")
            lines.append("")

        if len(matched_schemes) > 25:
            remaining = len(matched_schemes) - 25
            lines.append(f"*…and **{remaining}** more scheme(s). Refine your search to narrow down.*\n")

        lines.append("---\n💡 **Tip:** Tell me more about yourself (income, education, etc.) and I can find the **best** schemes for your specific situation!")

        return {"response": "\n".join(lines), "decision_report": {}, "action_plan": []}

    if settings.LOCAL_LLM_URL:
        try:
            # Adaptive: for 1 scheme, shorter prompt without comparison
            single_scheme = len(matched_schemes) == 1
            scheme_count_note = ""
            if single_scheme:
                scheme_count_note = "Only one scheme matched — no comparison needed."
            elif len(matched_schemes) > 5:
                scheme_count_note = f"There are {len(matched_schemes)} matched schemes. Prioritize the best 3-4."

            # Build rich context: group retrieved docs by scheme_id for each matched scheme
            docs_by_scheme = {}
            for doc in retrieved_docs:
                sid = doc.get("scheme_id")
                if sid not in docs_by_scheme:
                    docs_by_scheme[sid] = {"faqs": [], "chunks": []}
                if doc.get("type") == "faq":
                    docs_by_scheme[sid]["faqs"].append(f"Q: {doc.get('question','')}\nA: {doc.get('answer','')}")
                else:
                    docs_by_scheme[sid]["chunks"].append(doc.get("answer", ""))

            scheme_contexts = []
            for ms in matched_schemes[:4]:
                sid = ms.get("id")
                context = f"=== {ms['name']} ===\n"
                context += f"Benefits: {ms.get('benefits','')[:500]}\n"
                context += f"Eligibility: {ms.get('eligibility_text','')[:500]}\n"
                context += f"Documents: {(ms.get('documents_required','') or '')[:300]}\n"
                context += f"Process: {(ms.get('application_process','') or '')[:300]}\n"
                if sid and sid in docs_by_scheme:
                    d = docs_by_scheme[sid]
                    if d["faqs"]:
                        context += "FAQs:\n" + "\n".join(d["faqs"][:3]) + "\n"
                    if d["chunks"]:
                        context += "Details:\n" + "\n".join(d["chunks"][:3]) + "\n"
                scheme_contexts.append(context)

            scheme_context_str = "\n\n".join(scheme_contexts)

            prompt = f"""You are Sahayak AI, an expert on Indian government welfare schemes. Your role is to analyze REAL scheme data and provide accurate, grounded recommendations.

{conversation_context}
User Profile: {json.dumps(profile)}

{scheme_context_str}

{scheme_count_note}

CRITICAL INSTRUCTIONS — Read carefully:
1. Use ONLY the scheme data provided above — do NOT make up benefits, eligibility criteria, or amounts.
2. For each scheme, quote specific benefits, eligibility rules, and document requirements from the data.
3. Since the user is a resident of **{profile.get('state', 'India')}**, mention their state when discussing state-specific or central schemes.
4. **Pick ONE definitive best scheme** — do not list multiple options. Explain WHY it is the best using concrete details from the data.
5. Include key strengths and potential drawbacks based on actual eligibility rules vs user profile.
6. NEVER say "you qualify" — use "you may qualify" or "appears to be a good match".
7. Be professional, empathetic, and clear. 2-3 paragraphs.
8. If the data shows income limits, category requirements, or state restrictions, reference them specifically.
9. Start with "Based on your profile, I recommend **{{Scheme Name}}**" — be decisive."""
            text_response = await generate_text(prompt)

            top_scheme = matched_schemes[0]["name"] if matched_schemes else ""
            runner_up = matched_schemes[1]["name"] if len(matched_schemes) > 1 else ""

            decision_report = {
                "recommended_scheme": top_scheme,
                "recommendation_reasoning": "Based on your profile, this scheme offers the best alignment with your eligibility criteria.",
                "key_strengths": matched_schemes[0].get("benefits", "")[:300] if matched_schemes else "",
                "potential_drawbacks": "Verify all requirements on the official portal before applying.",
                "important_tradeoffs": f"Consider {runner_up} as an alternative if available." if runner_up else "No other schemes matched for comparison.",
                "runner_up": runner_up
            }

            return {"response": text_response, "decision_report": decision_report, "action_plan": []}
        except Exception as e:
            logger.error(f"AI Decision Advisor failed: {e}")

    response_lines = ["## 📋 Personalized Scheme Analysis\n"]
    for i, ms in enumerate(matched_schemes[:3]):
        badge = "🥇 Best Match" if i == 0 else (f"🥈 Option {i+1}" if i == 1 else f"🥉 Option {i+1}")
        response_lines.append(f"\n### {badge}: **{ms['name']}**")
        response_lines.append(f"💰 **Benefit**: {ms['benefits'][:200]}")
        response_lines.append(f"🏢 **Ministry**: {ms['ministry']}")
        if ms.get("match_reasons"):
            response_lines.append(f"✅ **Why it fits**: {'; '.join(ms['match_reasons'])}")

    response_lines.append("\n---\n⚠️ **Reminder**: This is an AI-generated analysis. Always verify with the official scheme portal.")

    top_scheme = matched_schemes[0]["name"] if matched_schemes else ""
    runner_up = matched_schemes[1]["name"] if len(matched_schemes) > 1 else ""

    decision_report = {
        "recommended_scheme": top_scheme,
        "recommendation_reasoning": "This scheme best matches your demographic and eligibility profile.",
        "key_strengths": matched_schemes[0].get("benefits", "")[:300] if matched_schemes else "",
        "potential_drawbacks": "Verify requirements on the official portal before proceeding.",
        "important_tradeoffs": f"You may also consider {runner_up} as an alternative." if runner_up else "No other matched schemes available for comparison.",
        "runner_up": runner_up
    }

    return {"response": "\n".join(response_lines), "decision_report": decision_report, "action_plan": []}


async def action_planner(state: AgentState) -> Dict[str, Any]:
    decision_report = state.get("decision_report", {})
    matched_schemes = state.get("matched_schemes", [])
    profile = state.get("profile", {})

    if not matched_schemes:
        return {"action_plan": []}

    top_scheme_name = decision_report.get("recommended_scheme") or matched_schemes[0]["name"]
    top_scheme = next((m for m in matched_schemes if m["name"] == top_scheme_name), matched_schemes[0])

    documents_text = top_scheme.get("documents_required", "")
    documents_list = [d.strip() for d in documents_text.split("\n") if d.strip()] if documents_text else [
        "Aadhaar Card",
        "Income Certificate",
        "Caste/Community Certificate (if applicable)",
        "Address Proof",
        "Bank Account Details",
        "Passport-size Photographs"
    ]

    action_plan = [
        {
            "step_number": 1,
            "action": "Gather Required Documents",
            "details": f"Prepare the following documents: {', '.join(documents_list[:5])}",
            "resource_link": "",
            "estimated_time": "1-2 days",
            "priority": "High"
        },
        {
            "step_number": 2,
            "action": f"Visit Official Portal for {top_scheme_name}",
            "details": "Go to the official scheme portal to read the latest guidelines and check application dates.",
            "resource_link": top_scheme.get("application_link", ""),
            "estimated_time": "30 minutes",
            "priority": "High"
        },
        {
            "step_number": 3,
            "action": "Complete Online Application",
            "details": "Fill in all required fields accurately. Double-check your personal details before submitting.",
            "resource_link": top_scheme.get("application_link", ""),
            "estimated_time": "1-2 hours",
            "priority": "High"
        },
        {
            "step_number": 4,
            "action": "Upload Documents",
            "details": "Upload scanned copies of all required documents. Ensure they are clear and legible.",
            "resource_link": "",
            "estimated_time": "30 minutes",
            "priority": "Medium"
        },
        {
            "step_number": 5,
            "action": "Submit & Track Application",
            "details": "Submit the application and save the acknowledgment/reference number for future tracking.",
            "resource_link": "",
            "estimated_time": "15 minutes",
            "priority": "Medium"
        },
        {
            "step_number": 6,
            "action": "Follow Up",
            "details": "Check application status periodically. Keep documents ready for verification if required.",
            "resource_link": "",
            "estimated_time": "Ongoing",
            "priority": "Low"
        }
    ]

    return {"action_plan": action_plan}


async def explanation_agent(state: AgentState) -> Dict[str, Any]:
    profile = state.get("profile", {})
    matched_schemes = state.get("matched_schemes", [])
    retrieved_docs = state.get("retrieved_docs", [])
    comparison_data = state.get("comparison_data", [])
    decision_report = state.get("decision_report", {})
    action_plan = state.get("action_plan", [])
    existing_response = state.get("response", "")

    # If decision_advisor already generated a response (LLM or deterministic), use it
    if existing_response and len(existing_response.strip()) > 50:
        return {"response": existing_response}

    # Build a grounded response from the actual retrieved scheme data
    user_state = profile.get("state", "India")
    lines = [f"## Personalized Scheme Analysis for **{user_state}**\n"]

    if decision_report.get("recommended_scheme"):
        rec = decision_report["recommended_scheme"]
        lines.append(f"### Recommended: **{rec}**")
        if decision_report.get("recommendation_reasoning"):
            lines.append(f"\n{decision_report['recommendation_reasoning']}")
        # Find the scheme in matched_schemes to pull real data
        top = next((s for s in matched_schemes if s["name"] == rec), matched_schemes[0] if matched_schemes else None)
        if top:
            if top.get("benefits"):
                lines.append(f"\n**Benefits:** {top['benefits'][:400]}")
            if top.get("eligibility_text"):
                lines.append(f"\n**Eligibility:** {top['eligibility_text'][:400]}")
            if top.get("documents_required"):
                docs_text = top["documents_required"][:300]
                lines.append(f"\n**Documents Required:** {docs_text}")
            if top.get("application_link"):
                lines.append(f"\n[Apply on Official Portal]({top['application_link']})")
        lines.append("")

    # Show other matched schemes with actual data
    if len(matched_schemes) > 1:
        lines.append("### Other Schemes You May Match\n")
        for s in matched_schemes[1:4]:
            lines.append(f"**{s['name']}** — {s.get('ministry', '')}")
            if s.get("benefits"):
                lines.append(f"> {s['benefits'][:200]}")
            if s.get("match_reasons"):
                lines.append(f"> ✓ {'; '.join(s['match_reasons'][:3])}")
            lines.append("")

    # Add relevant FAQ context if available
    faq_docs = [d for d in retrieved_docs if d.get("type") == "faq"][:3]
    if faq_docs:
        lines.append("### Quick Answers\n")
        for d in faq_docs:
            q = d.get("question", "")
            a = d.get("answer", "")
            if q and a:
                lines.append(f"**Q:** {q}")
                lines.append(f"**A:** {a[:200]}\n")

    if action_plan:
        lines.append("### Action Plan\n")
        for step in action_plan[:4]:
            lines.append(f"**Step {step['step_number']}**: {step['action']}")
            lines.append(f"> {step['details'][:200]}")
            if step.get("resource_link"):
                lines.append(f"> [Apply]({step['resource_link']})")
            lines.append("")

    return {"response": "\n".join(lines)}


async def responsible_ai_layer(state: AgentState) -> Dict[str, Any]:
    response = state.get("response", "")
    profile = state.get("profile", {})
    missing_fields = state.get("missing_fields", [])

    disclaimer = (
        "\n\n---\n"
        "⚠️ **Important Disclaimer**: Sahayak AI provides guidance based on official scheme rules. "
        "This is an AI-generated analysis and does not guarantee final eligibility or approval. "
        "Approval is subject to formal verification by the respective government department. "
        "**Always verify your eligibility on the official scheme portal before applying.**"
    )

    if "Important Disclaimer" not in response:
        response += disclaimer

    response = response.replace("You qualify for", "You may qualify for")
    response = response.replace("You are eligible for", "You appear to meet the criteria for")
    response = response.replace("you qualify", "you may qualify")
    response = response.replace("are eligible", "appear to be eligible")

    total_fields = 7
    completed_fields = total_fields - len(missing_fields)
    confidence = int((completed_fields / total_fields) * 100)
    confidence = max(20, min(100, confidence))

    return {
        "response": response,
        "confidence": confidence
    }

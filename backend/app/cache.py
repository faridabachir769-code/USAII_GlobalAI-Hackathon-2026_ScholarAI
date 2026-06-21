import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings

logger = logging.getLogger(__name__)

_redis = None
def _get_redis():
    global _redis
    if _redis is None and settings.REDIS_URL:
        import redis
        try:
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("Redis client connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Falling back to in-memory session cache.")
    return _redis

# Local In-Memory Session Storage
_memory_cache: Dict[str, str] = {}

# ── Profile (persistent via DB + ephemeral via cache) ─────────────────────

def get_profile(user_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    # Try DB first (persistent)
    if db is not None:
        try:
            from app.database import Profile
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if profile:
                data = profile.profile_data if isinstance(profile.profile_data, dict) else {}
                data["full_name"] = profile.full_name
                data["email"] = profile.email
                data["is_onboarded"] = profile.is_onboarded
                # Write-through to cache
                _memory_cache[user_id] = json.dumps(data)
                return data
        except Exception as e:
            logger.warning(f"DB profile lookup failed, using cache: {e}")

    # Fallback to Redis
    if _get_redis():
        try:
            data = _get_redis().get(f"session:{user_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")

    # Fallback to local memory cache
    data = _memory_cache.get(user_id)
    if data:
        return json.loads(data)
    return None


def set_profile(user_id: str, profile: Dict[str, Any], db: Optional[Session] = None, expire_seconds: int = 86400) -> bool:
    data_str = json.dumps(profile)

    # Persist to DB
    if db is not None:
        try:
            from app.database import Profile
            existing = db.query(Profile).filter(Profile.user_id == user_id).first()
            if existing:
                existing.profile_data = profile
                existing.full_name = profile.get("full_name", existing.full_name)
                existing.is_onboarded = True
                existing.updated_at = datetime.utcnow()
            else:
                db.add(Profile(
                    user_id=user_id,
                    full_name=profile.get("full_name"),
                    profile_data=profile,
                    is_onboarded=True
                ))
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"DB profile persist failed: {e}")

    # Write to Redis
    if _get_redis():
        try:
            _get_redis().setex(f"session:{user_id}", expire_seconds, data_str)
            return True
        except Exception as e:
            logger.error(f"Redis setex failed: {e}")

    # Fallback to local memory cache
    _memory_cache[user_id] = data_str
    return True

# ── Chat History (persistent via DB) ──────────────────────────────────────

def get_history(session_id: str, db: Optional[Session] = None) -> list:
    # Try DB first
    if db is not None:
        try:
            from app.database import ChatMessage
            msgs = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.id)
                .limit(100)
                .all()
            )
            if msgs:
                return [{"role": m.role, "content": m.content} for m in msgs]
        except Exception as e:
            logger.warning(f"DB history lookup failed: {e}")

    # Fallback to Redis
    hist_key = f"history:{session_id}"
    if _get_redis():
        try:
            data = _get_redis().get(hist_key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis history get failed: {e}")

    # Fallback to local memory cache
    data = _memory_cache.get(hist_key)
    if data:
        return json.loads(data)
    return []


def set_history(session_id: str, history: list, db: Optional[Session] = None, expire_seconds: int = 86400) -> bool:
    # Persist new messages to DB
    if db is not None:
        try:
            from app.database import ChatMessage
            recent = history[-2:] if len(history) > 2 else history
            for msg in recent:
                existing = (
                    db.query(ChatMessage)
                    .filter(
                        ChatMessage.session_id == session_id,
                        ChatMessage.role == msg.get("role"),
                        ChatMessage.content == msg.get("content")
                    )
                    .first()
                )
                if not existing:
                    db.add(ChatMessage(
                        session_id=session_id,
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    ))
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"DB history persist failed: {e}")

    # Write to Redis
    hist_key = f"history:{session_id}"
    data_str = json.dumps(history[-50:])  # Keep last 50
    if _get_redis():
        try:
            _get_redis().setex(hist_key, expire_seconds, data_str)
            return True
        except Exception as e:
            logger.error(f"Redis history setex failed: {e}")

    # Fallback to local memory cache
    _memory_cache[hist_key] = data_str
    return True

# ── pgmq Integration ──────────────────────────────────────────────────────

def enqueue_llm_job(job_type: str, payload: dict, priority: int = 5) -> Optional[int]:
    """Enqueue an async LLM job via pgmq."""
    if not settings.PGMQ_ENABLED:
        logger.info(f"pgmq disabled, skipping job: {job_type}")
        return None
    try:
        from sqlalchemy import text as sql_text
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(
                sql_text("SELECT pgmq.send('llm_jobs', :payload)"),
                {"payload": json.dumps({"job_type": job_type, **payload})}
            )
            db.commit()
            msg_id = result.scalar()
            logger.info(f"pgmq enqueued {job_type} job as msg_id={msg_id}")
            return msg_id
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"pgmq enqueue failed (non-fatal): {e}")
        return None


def consume_llm_jobs(batch_size: int = 5) -> List[dict]:
    """Consume pending LLM jobs from pgmq."""
    if not settings.PGMQ_ENABLED:
        return []
    try:
        from sqlalchemy import text as sql_text
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            rows = db.execute(
                sql_text("SELECT * FROM pgmq.read('llm_jobs', :batch, 30)"),
                {"batch": batch_size}
            ).fetchall()
            jobs = []
            for row in rows:
                jobs.append({
                    "msg_id": row[0],
                    "payload": json.loads(row[2]) if isinstance(row[2], str) else row[2],
                })
            return jobs
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"pgmq consume failed: {e}")
        return []


def delete_profile(user_id: str) -> bool:
    # Delete from Redis
    if _get_redis():
        try:
            _get_redis().delete(f"session:{user_id}")
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")

    # Delete from local memory
    if user_id in _memory_cache:
        del _memory_cache[user_id]

    # Delete from DB
    try:
        from app.database import SessionLocal, Profile
        db = SessionLocal()
        try:
            db.query(Profile).filter(Profile.user_id == user_id).delete()
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB profile delete failed: {e}")

    return True

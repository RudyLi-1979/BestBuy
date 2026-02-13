"""
Dependency injection functions for FastAPI
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal
import redis
from app.config import settings


def get_db() -> Generator[Session, None, None]:
    """
    Get database session
    Usage in route: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """
    Get Redis client
    Usage in route: redis_client = Depends(get_redis)
    """
    return redis.from_url(settings.redis_url, decode_responses=True)


def get_current_user_id(user_token: str = None) -> str:
    """
    Get current user ID from token (simplified version for MVP)
    For MVP, we use a guest user approach with UUID
    """
    if user_token:
        # TODO: Implement JWT token validation
        return user_token
    # Guest user - generate or use session-based ID
    import uuid
    return f"guest_{uuid.uuid4().hex[:8]}"

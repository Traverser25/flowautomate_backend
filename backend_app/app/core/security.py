# app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from typing import Any, Dict, Optional

from .config import get_settings

settings = get_settings()

# Password hashing context (bcrypt)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str) -> str:
    """Hash plain password using bcrypt"""
    return pwd_ctx.hash(password)


async def verify_password(password: str, hashed: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_ctx.verify(password, hashed)


async def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    """Create JWT access token"""
    now = datetime.now(timezone.utc)

    to_encode: Dict[str, Any] = {
        "sub": subject,   # user id
        "iat": int(now.timestamp()),  # issued at
    }
    if extra:
        to_encode.update(extra)

    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


async def decode_token(token: str) -> Dict[str, Any]:
    """Decode JWT token"""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])

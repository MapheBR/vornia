"""Security services for password hashing and JWT."""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

ACCESS_TOKEN_EXPIRE_HOURS = 24
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set")
    return secret


def hash_password(password: str) -> str:
    """Hash a plain text password."""
    hashed: str = pwd_context.hash(password)
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hash."""
    is_valid: bool = pwd_context.verify(plain_password, hashed_password)
    return is_valid


def create_access_token(
    *,
    user_id: str,
    email: str,
    company_id: str,
    role: str,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "company_id": company_id,
        "role": role,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, _jwt_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(token, _jwt_secret(), algorithms=[ALGORITHM])

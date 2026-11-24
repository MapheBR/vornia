"""FastAPI dependencies."""

from typing import Any

import jwt
from fastapi import Cookie, HTTPException, status

from vornia.services.security import decode_access_token


async def get_current_user(token: str | None = Cookie(None)) -> dict[str, Any]:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "company_id": payload["company_id"],
        "role": payload["role"],
    }

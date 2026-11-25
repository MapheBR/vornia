"""Common FastAPI dependencies (autenticação e rate limiting)."""

from typing import Any

from fastapi import Cookie, HTTPException, Request, status

from vornia.infrastructure.rate_limit import RateLimiter
from vornia.services.security import decode_access_token

# Substituível em testes; por padrão fail-open (sem Redis configurado).
_limiters: dict[str, RateLimiter] = {}


def configure_limiter(route: str, instance: RateLimiter) -> None:
    _limiters[route] = instance


def limiter_for(route: str) -> RateLimiter:
    return _limiters.get(route) or RateLimiter(None, limit=0, window_seconds=60)


async def enforce_rate_limit(request: Request, route: str) -> None:
    limiter = limiter_for(route)
    identifier = request.client.host if request.client else "unknown"
    if not await limiter.check(identifier, route):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas requisições. Tente novamente em instantes.",
            headers={"Retry-After": str(limiter.retry_after(identifier, route))},
        )


async def get_current_user(token: str | None = Cookie(None)) -> dict[str, Any]:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
    except Exception as exc:
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

"""Configuração do limitador e do cliente Redis."""

import os

import redis.asyncio as redis

from vornia.infrastructure.rate_limit import RateLimiter

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client  # noqa: PLW0603
    if _redis_client is None:
        url: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        _redis_client = redis.from_url(url)  # type: ignore[no-untyped-call]
    return _redis_client


def build_limiter(*, route: str, limit: int, window_seconds: int) -> RateLimiter:
    """Uma instância por rota (cada rota tem seu próprio limite)."""
    return RateLimiter(
        get_redis(),  # type: ignore[arg-type]
        limit=limit,
        window_seconds=window_seconds,
    )

"""Configura o limitador de requisições a partir do ambiente."""

import os

from vornia.dependencies import configure_limiter
from vornia.infrastructure.rate_limit import RateLimiter
from vornia.infrastructure.rate_limit_config import get_redis


def setup_rate_limit() -> None:
    """Habilita o limitador Redis quando RATE_LIMIT_ENABLED=true (padrão: on)."""
    if os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "false":
        return
    redis = get_redis()
    for route, limit in (
        ("login", 30),
        ("register", 30),
        ("refresh", 10),
        ("exports", 10),
        ("sync", 5),
        ("process", 5),
        ("edits", 20),
    ):
        configure_limiter(route, RateLimiter(redis, limit=limit, window_seconds=60))  # type: ignore[arg-type]

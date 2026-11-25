"""Testes do limitador de requisições baseado em Redis."""

import pytest

pytestmark = pytest.mark.unit


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expirations[key] = seconds

    async def ttl(self, key: str) -> int:
        return self.expirations.get(key, 0)


async def test_allows_requests_under_limit() -> None:
    from vornia.infrastructure.rate_limit import RateLimiter

    limiter = RateLimiter(FakeRedis(), limit=3, window_seconds=60)  # type: ignore[arg-type]
    assert await limiter.check("ip:1", "login") is True
    assert await limiter.check("ip:1", "login") is True


async def test_blocks_requests_over_limit() -> None:
    from vornia.infrastructure.rate_limit import RateLimiter

    limiter = RateLimiter(FakeRedis(), limit=2, window_seconds=60)  # type: ignore[arg-type]
    assert await limiter.check("ip:2", "login") is True
    assert await limiter.check("ip:2", "login") is True
    assert await limiter.check("ip:2", "login") is False


async def test_separate_routes_have_separate_buckets() -> None:
    from vornia.infrastructure.rate_limit import RateLimiter

    redis = FakeRedis()
    limiter = RateLimiter(redis, limit=1, window_seconds=60)  # type: ignore[arg-type]
    assert await limiter.check("ip:3", "login") is True
    assert await limiter.check("ip:3", "refresh") is True
    assert await limiter.check("ip:3", "login") is False


async def test_retry_after_is_remaining_window() -> None:
    from vornia.infrastructure.rate_limit import RateLimiter

    limiter = RateLimiter(FakeRedis(), limit=1, window_seconds=60)  # type: ignore[arg-type]
    await limiter.check("ip:4", "login")
    await limiter.check("ip:4", "login")
    assert limiter.retry_after("ip:4", "login") >= 1

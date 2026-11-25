"""Testes de integração do rate limiting nos endpoints de auth."""

import pytest
from httpx import ASGITransport, AsyncClient

from vornia.infrastructure.rate_limit import RateLimiter
from vornia.main import app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, key: str, seconds: int) -> object:
        return None

    async def ttl(self, key: str) -> int:
        return 60


@pytest.fixture(autouse=True)
def enforce_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limiters = {
        route: RateLimiter(FakeRedis(), limit=1, window_seconds=60)
        for route in ("login", "register", "refresh")
    }
    monkeypatch.setattr("vornia.dependencies._limiters", limiters)


async def test_login_returns_429_after_limit() -> None:
    payload = {"email": "alice@acme.example.com", "password": "wrong"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/api/v1/auth/login", json=payload)
        second = await client.post("/api/v1/auth/login", json=payload)

    assert first.status_code == 401
    assert second.status_code == 429
    assert "retry-after" in second.headers


async def test_refresh_returns_429_after_limit() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/api/v1/auth/refresh")
        second = await client.post("/api/v1/auth/refresh")

    assert first.status_code == 401
    assert second.status_code == 429

"""Integração do fluxo de refresh token, rotação, reuso e logout."""


import asyncpg
import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from vornia.main import app
from vornia.services.token import hash_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

BASE_URL = "http://test"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL)


async def _register_and_login(client: AsyncClient, email: str = "user@acme.example.com") -> dict:
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Acme",
            "email": email,
            "password": "strong-password",
            "full_name": "User",
        },
    )
    assert r.status_code == status.HTTP_201_CREATED
    return r.json()


async def test_register_sets_refresh_cookie() -> None:
    async with _client() as client:
        await _register_and_login(client)
        token = client.cookies.get("refresh_token")
        assert token is not None and len(token) >= 40


async def test_refresh_rotates_token_and_invalidates_old() -> None:
    async with _client() as client:
        await _register_and_login(client)
        old = client.cookies.get("refresh_token")
        assert old is not None

        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == status.HTTP_200_OK
        new = client.cookies.get("refresh_token")
        assert new is not None and new != old

        # token antigo agora é reuso -> 401
        client.cookies.set("refresh_token", old)
        reuse = await client.post("/api/v1/auth/refresh")
        assert reuse.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_without_cookie_returns_401() -> None:
    async with _client() as client:
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_revokes_refresh_token() -> None:
    async with _client() as client:
        await _register_and_login(client)
        token = client.cookies.get("refresh_token")
        assert token is not None

        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_200_OK
        assert client.cookies.get("refresh_token") is None

        client.cookies.set("refresh_token", token)
        after = await client.post("/api/v1/auth/refresh")
        assert after.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_hash_is_stored_not_plaintext() -> None:
    from tests.integration.conftest import resolve_bootstrap_database_url

    async with _client() as client:
        await _register_and_login(client)
        token = client.cookies.get("refresh_token")
        assert token is not None

    pool = await asyncpg.create_pool(resolve_bootstrap_database_url())
    try:
        async with pool.acquire() as conn:
            stored = await conn.fetchval("SELECT token_hash FROM refresh_tokens LIMIT 1")
            assert stored == hash_token(token)
            assert stored != token
    finally:
        await pool.close()


async def test_runtime_role_cannot_read_refresh_tokens() -> None:
    """vornia_app não tem GRANT na tabela refresh_tokens."""
    from tests.integration.conftest import resolve_app_database_url

    pool = await asyncpg.create_pool(resolve_app_database_url())
    try:
        async with pool.acquire() as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.fetchval("SELECT count(*) FROM refresh_tokens")
    finally:
        await pool.close()

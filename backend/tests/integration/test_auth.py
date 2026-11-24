"""Auth integration tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from vornia.main import app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_register_creates_company_user_and_sets_cookie() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Acme",
                "email": "alice@acme.example.com",
                "password": "strong-password",
                "full_name": "Alice",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@acme.example.com"
    assert data["full_name"] == "Alice"
    assert data["role"] == "admin"
    assert "id" in data
    assert "company_id" in data

    cookie = client.cookies.get("token")
    assert cookie is not None
    assert cookie != ""


async def test_login_with_valid_credentials_sets_cookie() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Acme",
                "email": "bob@acme.example.com",
                "password": "strong-password",
                "full_name": "Bob",
            },
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "bob@acme.example.com",
                "password": "strong-password",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "bob@acme.example.com"
    assert "id" in data
    assert "company_id" in data

    cookie = client.cookies.get("token")
    assert cookie is not None
    assert cookie != ""


async def test_login_with_invalid_credentials_returns_401() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Acme",
                "email": "charlie@acme.example.com",
                "password": "strong-password",
                "full_name": "Charlie",
            },
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "charlie@acme.example.com",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401


async def test_me_returns_authenticated_user() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Acme",
                "email": "diana@acme.example.com",
                "password": "strong-password",
                "full_name": "Diana",
            },
        )

        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "diana@acme.example.com"
    assert data["full_name"] == "Diana"
    assert data["role"] == "admin"


async def test_me_without_cookie_returns_401() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.cookies.clear()
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_tenant_isolation_user_cannot_see_other_company_data() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a:
        register_a = await client_a.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Company A",
                "email": "user-a@example.com",
                "password": "strong-password",
                "full_name": "User A",
            },
        )
        token_a = client_a.cookies.get("token")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_b:
        register_b = await client_b.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Company B",
                "email": "user-b@example.com",
                "password": "strong-password",
                "full_name": "User B",
            },
        )

    company_a_id = register_a.json()["company_id"]
    company_b_id = register_b.json()["company_id"]
    assert company_a_id != company_b_id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a:
        client_a.cookies.set("token", token_a)
        response = await client_a.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["company_id"] == company_a_id

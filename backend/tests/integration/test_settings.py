"""Company settings integration tests."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from vornia.main import app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _register_company(name: str, email: str) -> tuple[AsyncClient, dict[str, Any]]:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": name,
            "email": email,
            "password": "strong-password",
            "full_name": "Admin",
        },
    )
    assert response.status_code == 201
    return client, response.json()


async def test_put_and_get_settings() -> None:
    client, registration = await _register_company("Acme", "admin@acme.example.com")
    try:
        response = await client.put(
            "/api/v1/settings/timezone",
            json={"value": "America/Sao_Paulo"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "timezone"
        assert data["value"] == "America/Sao_Paulo"
        assert data["company_id"] == registration["company_id"]

        listed = await client.get("/api/v1/settings")
        assert listed.status_code == 200
        assert listed.json()["timezone"] == "America/Sao_Paulo"
    finally:
        await client.aclose()


async def test_put_settings_updates_existing_key() -> None:
    client, _ = await _register_company("Acme", "admin@acme.example.com")
    try:
        await client.put(
            "/api/v1/settings/workday_hours",
            json={"value": 8},
        )
        response = await client.put(
            "/api/v1/settings/workday_hours",
            json={"value": 8.8},
        )

        assert response.status_code == 200
        assert response.json()["value"] == 8.8
        listed = await client.get("/api/v1/settings")
        assert listed.json() == {"workday_hours": 8.8}
    finally:
        await client.aclose()


async def test_settings_are_isolated_per_tenant() -> None:
    client_a, _ = await _register_company("Company A", "admin-a@example.com")
    client_b, _ = await _register_company("Company B", "admin-b@example.com")
    try:
        await client_a.put(
            "/api/v1/settings/timezone",
            json={"value": "America/Sao_Paulo"},
        )
        await client_b.put(
            "/api/v1/settings/timezone",
            json={"value": "UTC"},
        )

        listed_a = await client_a.get("/api/v1/settings")
        listed_b = await client_b.get("/api/v1/settings")

        assert listed_a.json() == {"timezone": "America/Sao_Paulo"}
        assert listed_b.json() == {"timezone": "UTC"}
    finally:
        await client_a.aclose()
        await client_b.aclose()


async def test_delete_settings() -> None:
    client, _ = await _register_company("Acme", "admin@acme.example.com")
    try:
        await client.put("/api/v1/settings/timezone", json={"value": "UTC"})

        response = await client.delete("/api/v1/settings/timezone")

        assert response.status_code == 204
        listed = await client.get("/api/v1/settings")
        assert listed.json() == {}
    finally:
        await client.aclose()


async def test_get_unknown_setting_returns_404() -> None:
    client, _ = await _register_company("Acme", "admin@acme.example.com")
    try:
        response = await client.get("/api/v1/settings/does-not-exist")

        assert response.status_code == 404
    finally:
        await client.aclose()


async def test_settings_require_authentication() -> None:
    client, _ = await _register_company("Acme", "admin@acme.example.com")
    try:
        client.cookies.clear()

        response = await client.get("/api/v1/settings")

        assert response.status_code == 401
    finally:
        await client.aclose()

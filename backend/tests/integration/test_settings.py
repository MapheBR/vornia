"""Integração da API de settings: allowlist, defaults, persistência e isolamento."""

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from vornia.main import app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

BASE_URL = "http://test"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL)


async def _register(client: AsyncClient, company: str, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": company,
            "email": email,
            "password": "strong-password",
            "full_name": "Admin",
        },
    )
    assert r.status_code == status.HTTP_201_CREATED


async def test_list_settings_returns_defaults() -> None:
    async with _client() as client:
        await _register(client, "Acme", "admin@acme.example.com")
        response = await client.get("/api/v1/settings")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["timezone"] == "America/Sao_Paulo"
    assert data["workday_minutes"] == 480
    assert data["overtime_enabled"] is False


async def test_put_get_and_delete_setting() -> None:
    async with _client() as client:
        await _register(client, "Acme", "admin@acme.example.com")
        put = await client.put("/api/v1/settings/timezone", json={"value": "Europe/London"})
        assert put.status_code == status.HTTP_200_OK
        assert put.json()["value"] == "Europe/London"

        got = await client.get("/api/v1/settings/timezone")
        assert got.json()["value"] == "Europe/London"

        listed = await client.get("/api/v1/settings")
        assert listed.json()["data"]["timezone"] == "Europe/London"

        deleted = await client.delete("/api/v1/settings/timezone")
        assert deleted.status_code == status.HTTP_204_NO_CONTENT

        after = await client.get("/api/v1/settings/timezone")
        assert after.json()["value"] == "America/Sao_Paulo"


async def test_unknown_key_is_rejected() -> None:
    async with _client() as client:
        await _register(client, "Acme", "admin@acme.example.com")
        response = await client.put("/api/v1/settings/unknown_key", json={"value": "x"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_invalid_value_type_is_rejected() -> None:
    async with _client() as client:
        await _register(client, "Acme", "admin@acme.example.com")
        response = await client.put("/api/v1/settings/workday_minutes", json={"value": "muitas"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_settings_are_isolated_per_tenant() -> None:
    async with _client() as client_a:
        await _register(client_a, "Company A", "admin-a@acme.example.com")
        await client_a.put("/api/v1/settings/timezone", json={"value": "America/Sao_Paulo"})
        company_a_id = (await client_a.get("/api/v1/auth/me")).json()["company_id"]

    async with _client() as client_b:
        await _register(client_b, "Company B", "admin-b@acme.example.com")
        listed = await client_b.get("/api/v1/settings")
        assert listed.json()["data"]["timezone"] == "America/Sao_Paulo"
        assert (await client_b.get("/api/v1/auth/me")).json()["company_id"] != company_a_id

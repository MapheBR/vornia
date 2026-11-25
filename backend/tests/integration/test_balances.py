"""Testes de integração dos endpoints de banco de horas e feriados."""

import json

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from vornia.main import app
from vornia.services.security import create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _app_url() -> str:
    from tests.integration.conftest import resolve_app_database_url

    return resolve_app_database_url()


def _bootstrap_url() -> str:
    from tests.integration.conftest import resolve_bootstrap_database_url

    return resolve_bootstrap_database_url()


@pytest.fixture
async def tenant():  # type: ignore[no-untyped-def]
    bootstrap = await asyncpg.create_pool(_bootstrap_url())
    app_pool = await asyncpg.create_pool(_app_url())
    company_id = ""
    try:
        async with bootstrap.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO companies (name, slug) VALUES ('Balanco', 'bal-' || gen_random_uuid()::text) RETURNING id"
            )
            company_id = str(row["id"])
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            employee = await conn.fetchval(
                "INSERT INTO employees (company_id, name) VALUES ($1,'Maria') RETURNING id",
                company_id,
            )
        yield company_id, str(employee)
    finally:
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            for table in ("time_balances", "holidays", "employees"):
                await conn.execute(f"DELETE FROM {table} WHERE company_id = $1", company_id)
        async with bootstrap.acquire() as conn:
            await conn.execute("DELETE FROM audit_logs WHERE company_id = $1", company_id)
            await conn.execute("DELETE FROM companies WHERE id = $1", company_id)
        await app_pool.close()
        await bootstrap.close()


def _client(company_id: str) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    client.cookies.set(
        "token",
        create_access_token(
            user_id="00000000-0000-4000-8000-000000000001",
            email="bal@acme.example.com",
            company_id=company_id,
            role="admin",
        ),
    )
    return client


async def test_recalculate_creates_balance(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _ = tenant
    async with _client(company_id) as client:
        response = await client.post("/api/v1/balances/recalculate", json={"month": "2026-11"})
    assert response.status_code == 200
    assert "recalculated" in response.json()


async def test_list_balances(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _ = tenant
    async with _client(company_id) as client:
        await client.post("/api/v1/balances/recalculate", json={"month": "2026-11"})
        response = await client.get("/api/v1/balances")
    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_holidays_crud(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _ = tenant
    async with _client(company_id) as client:
        created = await client.post(
            "/api/v1/holidays",
            json={"date": "2026-12-25", "name": "Natal", "jornada_especial_hours": 4.0},
        )
        assert created.status_code == 201
        listed = await client.get("/api/v1/holidays")
        assert listed.status_code == 200
        assert listed.json()["data"][0]["name"] == "Natal"

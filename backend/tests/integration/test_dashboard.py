"""Testes de integração do dashboard (agregações isoladas por tenant)."""

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
                "INSERT INTO companies (name, slug) VALUES ('Dash', 'dash-' || gen_random_uuid()::text) RETURNING id"
            )
            company_id = str(row["id"])
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            await conn.execute(
                "INSERT INTO employees (company_id, name) VALUES ($1,'Maria')", company_id
            )
            await conn.execute(
                """
                INSERT INTO processed_journeys
                    (company_id, employee_id, date, worked_hours, expected_hours, status)
                SELECT $1, id, '2026-11-25', 8.0, 8.0, 'complete' FROM employees WHERE company_id = $1
                """,
                company_id,
            )
            await conn.execute(
                """
                INSERT INTO processed_journeys
                    (company_id, employee_id, date, worked_hours, expected_hours, status)
                SELECT $1, id, '2026-11-24', 6.0, 8.0, 'inconsistency' FROM employees WHERE company_id = $1
                """,
                company_id,
            )
        yield company_id
    finally:
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            for table in ("processed_journeys", "employees"):
                await conn.execute(f"DELETE FROM {table} WHERE company_id = $1", company_id)
        async with bootstrap.acquire() as conn:
            await conn.execute("DELETE FROM companies WHERE id = $1", company_id)
        await app_pool.close()
        await bootstrap.close()


def _client(company_id: str) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    client.cookies.set(
        "token",
        create_access_token(
            user_id="00000000-0000-4000-8000-000000000001",
            email="dash@acme.example.com",
            company_id=company_id,
            role="admin",
        ),
    )
    return client


async def test_summary_aggregates_tenant_data(tenant) -> None:  # type: ignore[no-untyped-def]
    async with _client(tenant) as client:
        response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_employees"] == 1
    assert data["hours_worked"] == pytest.approx(14.0)
    assert data["inconsistencies"] == 1


async def test_inconsistencies_list(tenant) -> None:  # type: ignore[no-untyped-def]
    async with _client(tenant) as client:
        response = await client.get("/api/v1/dashboard/inconsistencies")
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 1
    assert rows[0]["status"] == "inconsistency"

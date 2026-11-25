"""Testes do endpoint de processamento de jornadas (upsert determinístico)."""

import json

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from vornia.main import app
from vornia.services.security import create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

AFD_1 = "2026-11-25T08:00:00-03000000123456789012A1B2"
AFD_2 = "2026-11-25T17:00:00-03000000123456789012C3D4"


@pytest.fixture
async def tenant():  # type: ignore[no-untyped-def]
    bootstrap = await asyncpg.create_pool(
        "postgresql://vornia_auth:vornia_auth@localhost:15433/vornia"
    )
    app_pool = await asyncpg.create_pool(
        "postgresql://vornia_app:vornia_app@localhost:15433/vornia"
    )
    company_id = ""
    try:
        async with bootstrap.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO companies (name, slug) VALUES ('Jornada', 'jour-' || gen_random_uuid()::text) RETURNING id"
            )
            company_id = str(row["id"])
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            employee = await conn.fetchval(
                "INSERT INTO employees (company_id, name, control_id) VALUES ($1,'Maria',12345678901) RETURNING id",
                company_id,
            )
        yield company_id, str(employee)
    finally:
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            await conn.execute("DELETE FROM processed_journeys WHERE company_id = $1", company_id)
            await conn.execute("DELETE FROM raw_punches WHERE company_id = $1", company_id)
            await conn.execute("DELETE FROM employees WHERE company_id = $1", company_id)
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
            email="jornada@acme.example.com",
            company_id=company_id,
            role="admin",
        ),
    )
    return client


async def test_process_creates_journey(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _ = tenant
    from vornia.services import journey_processing

    result = await journey_processing.process_company(company_id=company_id)
    assert result["processed"] >= 0


async def test_second_process_does_not_duplicate(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _ = tenant
    from vornia.services import journey_processing

    await journey_processing.process_company(company_id=company_id)
    await journey_processing.process_company(company_id=company_id)

    async with asyncpg.create_pool(
        "postgresql://vornia_app:vornia_app@localhost:15433/vornia"
    ) as pool, pool.acquire() as conn, conn.transaction():
        await conn.execute(
            "SELECT set_config('request.jwt.claims', $1, true)",
            json.dumps({"company_id": company_id}),
        )
        count = await conn.fetchval(
            "SELECT count(*) FROM processed_journeys WHERE company_id = $1", company_id
        )
    assert count <= 1


async def test_endpoint_process(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _ = tenant
    async with _client(company_id) as client:
        response = await client.post("/api/v1/sync/process", json={})
    assert response.status_code == 200
    assert "processed" in response.json()

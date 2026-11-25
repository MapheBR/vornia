"""Testes da edição manual com cascata atômica (matriz 18–22)."""

import json

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from vornia.main import app
from vornia.services import manual_edit
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
                "INSERT INTO companies (name, slug) VALUES ('Edicao', 'edit-' || gen_random_uuid()::text) RETURNING id"
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
            punch = await conn.fetchval(
                """
                INSERT INTO raw_punches (company_id, employee_id, punched_at, source, external_id)
                VALUES ($1,$2,'2026-11-25T08:00:00+00:00','controlid','p-1') RETURNING id
                """,
                company_id,
                employee,
            )
        yield company_id, str(employee), str(punch)
    finally:
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": company_id}),
            )
            for table in ("processed_journeys", "raw_punches", "employees"):
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
            email="edit@acme.example.com",
            company_id=company_id,
            role="admin",
        ),
    )
    return client


async def test_reason_is_required(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _, punch = tenant
    async with _client(company_id) as client:
        response = await client.patch(
            f"/api/v1/raw-punches/{punch}", json={"punched_at": "2026-11-25T09:00:00+00:00"}
        )
    assert response.status_code == 422


async def test_cascade_creates_journey_and_audit(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _, punch = tenant
    async with _client(company_id) as client:
        response = await client.patch(
            f"/api/v1/raw-punches/{punch}",
            json={"punched_at": "2026-11-25T09:00:00+00:00", "reason": "Ajuste de batida"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["recalculated"] is True


async def test_atomic_rollback_on_failure(tenant, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Falha induzida no recálculo: nada é persistido (nem o audit log)."""
    company_id, _, punch = tenant

    async def broken_recalculate(*args: object, **kwargs: object) -> None:  # noqa: ARG001
        raise RuntimeError("falha induzida")

    monkeypatch.setattr(manual_edit, "recalculate_for_punch", broken_recalculate)
    with pytest.raises(RuntimeError, match="induzida"):
        await manual_edit.edit_punch(
            company_id=company_id,
            punch_id=punch,
            punched_at="2026-11-25T10:00:00+00:00",
            reason="Teste de rollback",
            changed_by="00000000-0000-4000-8000-000000000001",
        )

    pool = await asyncpg.create_pool(_app_url())
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            "SELECT set_config('request.jwt.claims', $1, true)",
            json.dumps({"company_id": company_id}),
        )
        punched = await conn.fetchval("SELECT punched_at FROM raw_punches WHERE id = $1", punch)
        logs = await conn.fetchval(
            "SELECT count(*) FROM audit_logs WHERE company_id = $1", company_id
        )
    await pool.close()
    assert str(punched) != "2026-11-25 10:00:00+00:00"
    assert logs == 0


async def test_audit_logs_append_only(tenant) -> None:  # type: ignore[no-untyped-def]
    company_id, _, punch = tenant
    async with _client(company_id) as client:
        await client.patch(
            f"/api/v1/raw-punches/{punch}",
            json={"punched_at": "2026-11-25T09:00:00+00:00", "reason": "Ajuste válido"},
        )
        logs = await client.get("/api/v1/audit-logs")
    assert logs.status_code == 200
    assert logs.json()["data"][0]["reason"] == "Ajuste válido"

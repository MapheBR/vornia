"""Testes de integração da sincronização de batidas do Control iD."""

from typing import Any

import asyncpg
import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from vornia.main import app
from vornia.services import controlid_sync

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

AFD_LINES = [
    "2026-11-25T08:00:00-03000000123456789012A1B2",
    "2026-11-25T17:00:00-03000000123456789012C3D4",
    "2026-11-25T18:00:00-03000999999999999999FF01",  # código sem funcionário
]


def _app_url() -> str:
    from tests.integration.conftest import resolve_app_database_url

    return resolve_app_database_url()


def _bootstrap_url() -> str:
    from tests.integration.conftest import resolve_bootstrap_database_url

    return resolve_bootstrap_database_url()


@pytest.fixture
async def tenant():  # type: ignore[no-untyped-def]
    import json

    bootstrap = await asyncpg.create_pool(_bootstrap_url())
    app_pool = await asyncpg.create_pool(_app_url())
    company_id = ""
    try:
        async with bootstrap.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO companies (name, slug) VALUES ('Sync', 'sync-4-' || gen_random_uuid()::text) RETURNING id"
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
        yield company_id, str(employee), AFD_LINES
    finally:
        try:
            async with app_pool.acquire() as conn, conn.transaction():
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    json.dumps({"company_id": company_id}),
                )
                await conn.execute("DELETE FROM raw_punches WHERE company_id = $1", company_id)
                await conn.execute("DELETE FROM sync_state WHERE company_id = $1", company_id)
                await conn.execute("DELETE FROM employees WHERE company_id = $1", company_id)
            async with bootstrap.acquire() as conn:
                await conn.execute("DELETE FROM companies WHERE id = $1", company_id)
        finally:
            await app_pool.close()
            await bootstrap.close()


async def _fake_fetch(*args: Any, **kwargs: Any) -> list[str]:  # noqa: ARG001
    return AFD_LINES


async def test_sync_inserts_punches_and_flags_unmapped(tenant, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    company_id, _, _ = tenant
    monkeypatch.setattr(controlid_sync, "fetch_punches", _fake_fetch)

    result = await controlid_sync.sync_company(company_id=company_id, full=True)
    assert result["inserted"] == 3
    assert result["unmapped"] == 1
    assert result["failed"] == 0


async def test_sync_is_idempotent(tenant, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    company_id, _, _ = tenant
    monkeypatch.setattr(controlid_sync, "fetch_punches", _fake_fetch)

    first = await controlid_sync.sync_company(company_id=company_id, full=True)
    second = await controlid_sync.sync_company(company_id=company_id, full=True)

    assert first["inserted"] == 3
    assert second["inserted"] == 0
    assert second["skipped"] == 3


async def test_sync_state_persists_cursor(tenant, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    company_id, _, _ = tenant

    async def empty_fetch(*args: Any, **kwargs: Any) -> list[str]:  # noqa: ARG001
        return []

    monkeypatch.setattr(controlid_sync, "fetch_punches", empty_fetch)
    await controlid_sync.sync_company(company_id=company_id, full=False)

    state = await controlid_sync.get_sync_state(company_id=company_id)
    assert state is not None
    assert state["resource"] == "punches"
    assert state["status"] == "success"


async def test_endpoint_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/sync/controlid", json={"full": True})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

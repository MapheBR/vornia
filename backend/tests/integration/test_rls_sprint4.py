"""Provas de que as tabelas do Sprint 4 também respeitam FORCE RLS."""

import json
import os

import asyncpg
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

TABLES = ("raw_punches", "processed_journeys", "sync_state")


@pytest.mark.parametrize("table", TABLES)
async def test_rls_is_forced(table: str) -> None:
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT c.relrowsecurity AS rls, c.relforcerowsecurity AS forced
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = $1
                """,
                table,
            )
    finally:
        await pool.close()

    assert row is not None, f"tabela {table} não existe"
    assert row["rls"] is True
    assert row["forced"] is True


async def test_runtime_role_cannot_see_other_tenant_punches() -> None:
    """Com claims de A, batidas de B são invisíveis (RLS no banco)."""
    bootstrap = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        async with bootstrap.acquire() as conn, conn.transaction():
            await conn.execute(
                """
                INSERT INTO companies (name, slug)
                VALUES ('Pula A', 'pula-a-4'), ('Pula B', 'pula-b-4')
                ON CONFLICT (slug) DO NOTHING
                """
            )
            rows = await conn.fetch(
                "SELECT id FROM companies WHERE slug IN ('pula-a-4','pula-b-4') ORDER BY slug"
            )
            company_a, company_b = str(rows[0]["id"]), str(rows[1]["id"])

        async with app_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    json.dumps({"company_id": company_a}),
                )
                employee = await conn.fetchval(
                    "INSERT INTO employees (company_id, name) VALUES ($1,'Pula') RETURNING id",
                    company_a,
                )
                await conn.execute(
                    """
                    INSERT INTO raw_punches (company_id, employee_id, punched_at, source, external_id)
                    VALUES ($1, $2, now(), 'controlid', 'a-1')
                    """,
                    company_a,
                    employee,
                )
            async with conn.transaction():
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    json.dumps({"company_id": company_b}),
                )
                await conn.execute(
                    """
                    INSERT INTO raw_punches (company_id, punched_at, source, external_id)
                    VALUES ($1, now(), 'controlid', 'b-1')
                    """,
                    company_b,
                )

            async with conn.transaction():
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    json.dumps({"company_id": company_a}),
                )
                visible = await conn.fetchval("SELECT count(*) FROM raw_punches")
                by_foreign = await conn.fetchval(
                    "SELECT count(*) FROM raw_punches WHERE external_id = 'b-1'"
                )
    finally:
        await app_pool.close()
        await bootstrap.close()

    assert visible == 1
    assert by_foreign == 0

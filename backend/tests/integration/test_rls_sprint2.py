"""RLS enforcement for the Sprint 2 tables (employees and settings)."""

import json
import os

import asyncpg
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

TENANT_TABLES = ("employees", "settings")


async def _seed_two_tenants(bootstrap: asyncpg.Pool) -> dict[str, str]:
    async with bootstrap.acquire() as conn, conn.transaction():
        company_a = await conn.fetchval(
            "INSERT INTO companies (name, slug) VALUES ($1, $2) RETURNING id",
            "Tenant A",
            "tenant-a",
        )
        company_b = await conn.fetchval(
            "INSERT INTO companies (name, slug) VALUES ($1, $2) RETURNING id",
            "Tenant B",
            "tenant-b",
        )
        await conn.execute(
            "INSERT INTO employees (company_id, name) VALUES ($1, $2)",
            company_a,
            "Employee A",
        )
        await conn.execute(
            "INSERT INTO employees (company_id, name) VALUES ($1, $2)",
            company_b,
            "Employee B",
        )
        await conn.execute(
            "INSERT INTO settings (company_id, key, value) VALUES ($1, $2, $3)",
            company_a,
            "timezone",
            json.dumps("America/Sao_Paulo"),
        )
        await conn.execute(
            "INSERT INTO settings (company_id, key, value) VALUES ($1, $2, $3)",
            company_b,
            "timezone",
            json.dumps("UTC"),
        )

    return {"company_a": str(company_a), "company_b": str(company_b)}


async def test_rls_is_forced_on_sprint2_tables() -> None:
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        async with app_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY($1::text[])
                """,
                list(TENANT_TABLES),
            )
            owned = await conn.fetchval(
                """
                SELECT count(*)
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY($1::text[])
                  AND pg_get_userbyid(c.relowner) = current_user
                """,
                list(TENANT_TABLES),
            )
    finally:
        await app_pool.close()

    assert len(rows) == len(TENANT_TABLES)
    for row in rows:
        assert row["relrowsecurity"] is True, row["relname"]
        assert row["relforcerowsecurity"] is True, row["relname"]
    assert owned == 0


async def test_app_role_sees_only_its_own_tenant_rows() -> None:
    bootstrap = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        ids = await _seed_two_tenants(bootstrap)
        async with app_pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"company_id": ids["company_a"]}),
            )
            employees = await conn.fetch("SELECT name FROM employees")
            settings = await conn.fetch("SELECT value FROM settings")
    finally:
        await app_pool.close()
        await bootstrap.close()

    assert [row["name"] for row in employees] == ["Employee A"]
    assert [json.loads(row["value"]) for row in settings] == ["America/Sao_Paulo"]


async def test_app_role_sees_nothing_without_claims() -> None:
    bootstrap = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        await _seed_two_tenants(bootstrap)
        async with app_pool.acquire() as conn, conn.transaction():
            employees = await conn.fetchval("SELECT count(*) FROM employees")
            settings = await conn.fetchval("SELECT count(*) FROM settings")
    finally:
        await app_pool.close()
        await bootstrap.close()

    assert employees == 0
    assert settings == 0

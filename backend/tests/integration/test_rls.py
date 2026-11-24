"""Provam que o RLS isola tenants no nivel do banco, nao no codigo Python."""

import json
import os

import asyncpg
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


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
        user_a = await conn.fetchval(
            "INSERT INTO users (email, password_hash, full_name) VALUES ($1, $2, $3) RETURNING id",
            "user-a@tenant-a.example.com",
            "hash",
            "User A",
        )
        user_b = await conn.fetchval(
            "INSERT INTO users (email, password_hash, full_name) VALUES ($1, $2, $3) RETURNING id",
            "user-b@tenant-b.example.com",
            "hash",
            "User B",
        )
        await conn.execute(
            "INSERT INTO company_users (company_id, user_id, role) VALUES ($1, $2, $3)",
            company_a,
            user_a,
            "admin",
        )
        await conn.execute(
            "INSERT INTO company_users (company_id, user_id, role) VALUES ($1, $2, $3)",
            company_b,
            user_b,
            "admin",
        )

    return {
        "company_a": str(company_a),
        "company_b": str(company_b),
        "user_a": str(user_a),
        "user_b": str(user_b),
    }


async def _with_claims(
    app_pool: asyncpg.Pool,
    claims: dict[str, str] | None,
) -> tuple[int, int, int]:
    """Executa contagens dentro de uma transacao com (ou sem) claims."""
    async with app_pool.acquire() as conn, conn.transaction():
        if claims is not None:
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps(claims),
            )
        companies = await conn.fetchval("SELECT count(*) FROM companies")
        company_users = await conn.fetchval("SELECT count(*) FROM company_users")
        users = await conn.fetchval("SELECT count(*) FROM users")
    return int(companies), int(company_users), int(users)


async def test_app_role_cannot_bypass_rls() -> None:
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        async with app_pool.acquire() as conn:
            attributes = await conn.fetchrow(
                """
                SELECT r.rolsuper, r.rolbypassrls
                FROM pg_roles r
                WHERE r.rolname = current_user
                """
            )
            assert attributes is not None
            assert attributes["rolsuper"] is False
            assert attributes["rolbypassrls"] is False

            owned = await conn.fetchval(
                """
                SELECT count(*)
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname IN ('companies', 'users', 'company_users')
                  AND pg_get_userbyid(c.relowner) = current_user
                """
            )
            assert owned == 0
    finally:
        await app_pool.close()


async def test_rls_is_forced_on_tenant_tables() -> None:
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        async with app_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname IN ('companies', 'users', 'company_users')
                """
            )
    finally:
        await app_pool.close()

    assert len(rows) == 3
    for row in rows:
        assert row["relrowsecurity"] is True, row["relname"]
        assert row["relforcerowsecurity"] is True, row["relname"]


async def test_app_role_sees_only_its_own_tenant() -> None:
    bootstrap = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        ids = await _seed_two_tenants(bootstrap)

        companies, company_users, users = await _with_claims(
            app_pool, {"company_id": ids["company_a"]}
        )

    finally:
        await app_pool.close()
        await bootstrap.close()

    assert companies == 1
    assert company_users == 1
    assert users == 1


async def test_app_role_sees_nothing_without_claims() -> None:
    bootstrap = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        await _seed_two_tenants(bootstrap)

        companies, company_users, users = await _with_claims(app_pool, None)

    finally:
        await app_pool.close()
        await bootstrap.close()

    assert companies == 0
    assert company_users == 0
    assert users == 0


async def test_no_claims_on_reused_connection_returns_zero_rows() -> None:
    """Depois de uma transacao com claims, a mesma conexao sem claims ve zero.

    Apos o fim de uma transacao que usou `set_config(..., true)`, o GUC fica
    como string vazia. A policy precisa tratar isso como ausencia de claim
    (0 linhas) e nao como JSON invalido (erro).
    """
    bootstrap = await asyncpg.create_pool(os.environ["DATABASE_URL_BOOTSTRAP"])
    app_pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"], min_size=1, max_size=1)
    try:
        ids = await _seed_two_tenants(bootstrap)

        async with app_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "SELECT set_config('request.jwt.claims', $1, true)",
                    json.dumps({"company_id": ids["company_a"]}),
                )
                assert await conn.fetchval("SELECT count(*) FROM companies") == 1

            companies = await conn.fetchval("SELECT count(*) FROM companies")
            company_users = await conn.fetchval("SELECT count(*) FROM company_users")
            users = await conn.fetchval("SELECT count(*) FROM users")

    finally:
        await app_pool.close()
        await bootstrap.close()

    assert companies == 0
    assert company_users == 0
    assert users == 0

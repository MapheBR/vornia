"""Testes de RLS das tabelas do Sprint 5 (holidays, time_balances, audit_logs)."""

import os

import asyncpg
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

TABLES = ("holidays", "time_balances", "audit_logs")


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


async def test_audit_logs_is_append_only() -> None:
    """Nenhuma policy de UPDATE/DELETE em audit_logs."""
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL_APP"])
    try:
        async with pool.acquire() as conn:
            commands = await conn.fetch(
                """
                SELECT p.polcmd FROM pg_policy p
                JOIN pg_class c ON c.oid = p.polrelid
                WHERE c.relname = 'audit_logs'
                """
            )
    finally:
        await pool.close()
    cmds = {row["polcmd"] for row in commands}
    assert "w" not in cmds  # UPDATE
    assert "d" not in cmds  # DELETE

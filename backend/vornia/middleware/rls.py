"""Row Level Security context helpers."""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from vornia.infrastructure.database import get_bootstrap_pool, get_db_pool


async def set_rls_context(conn: asyncpg.Connection, claims: dict[str, Any]) -> None:
    """Set the request.jwt.claims configuration parameter for RLS.

    The policies read `current_setting('request.jwt.claims', true)::json`,
    so the claims must be stored as JSON text.
    """
    await conn.execute(
        "SELECT set_config('request.jwt.claims', $1, true)",
        json.dumps(claims),
    )


@asynccontextmanager
async def rls_connection(
    claims: dict[str, Any] | None = None,
) -> AsyncGenerator[asyncpg.Connection, None]:
    """Acquire a runtime connection with the tenant context set."""
    pool = await get_db_pool()
    async with pool.acquire() as conn, conn.transaction():
        if claims:
            await set_rls_context(conn, claims)
        yield conn


@asynccontextmanager
async def bootstrap_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Acquire a bootstrap connection for tenant creation and login.

    Runs as a role with BYPASSRLS. `SET LOCAL row_security = off` is kept as a
    fail-closed guard: it errors out if this ever runs on a role that cannot
    bypass RLS.
    """
    pool = await get_bootstrap_pool()
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute("SET LOCAL row_security = off;")
        yield conn

"""Company settings repository (asyncpg, parameterized queries only)."""

import json
from typing import Any

import asyncpg

_COLUMNS = "id, company_id, key, value, created_at, updated_at"
# SQL estatico montado apenas com constantes deste modulo; valores do usuario
# sempre entram como parametros ligados ($1, $2, $3).
UPSERT_SQL = (
    "INSERT INTO settings (company_id, key, value) VALUES ($1, $2, $3::jsonb) "  # nosec B608
    "ON CONFLICT (company_id, key) DO UPDATE SET value = EXCLUDED.value, updated_at = now() "
    "RETURNING " + _COLUMNS
)
LIST_SQL = "SELECT " + _COLUMNS + " FROM settings ORDER BY key"  # nosec B608
GET_SQL = "SELECT " + _COLUMNS + " FROM settings WHERE key = $1"  # nosec B608


async def upsert(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    key: str,
    value: Any,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        UPSERT_SQL,
        company_id,
        key,
        json.dumps(value),
    )
    return dict(row) if row else {}


async def list_all(conn: asyncpg.Connection) -> dict[str, Any]:
    rows = await conn.fetch(LIST_SQL)
    return {row["key"]: row["value"] for row in rows}


async def get_by_key(conn: asyncpg.Connection, key: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(GET_SQL, key)
    return dict(row) if row else None


async def delete(conn: asyncpg.Connection, key: str) -> bool:
    result = await conn.execute("DELETE FROM settings WHERE key = $1", key)
    return bool(result.endswith("1"))

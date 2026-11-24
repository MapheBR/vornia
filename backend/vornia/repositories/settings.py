"""Repositório de settings por empresa."""

import json
from typing import Any

import asyncpg


def _decode(value: Any) -> Any:
    """asyncpg devolve JSONB como string; desserializa quando necessário."""
    return json.loads(value) if isinstance(value, str) else value


def _deserialize(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "value": _decode(row["value"])}


async def upsert_setting(
    conn: asyncpg.Connection, *, company_id: str, key: str, value: Any
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        INSERT INTO settings (company_id, key, value)
        VALUES ($1, $2, $3::jsonb)
        ON CONFLICT (company_id, key)
        DO UPDATE SET value = EXCLUDED.value, updated_at = now()
        RETURNING key, value, updated_at
        """,
        company_id,
        key,
        __import__("json").dumps(value),
    )
    return dict(row) if row else None


async def get_setting(
    conn: asyncpg.Connection, *, company_id: str, key: str
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT key, value FROM settings WHERE company_id = $1 AND key = $2",
        company_id,
        key,
    )
    return _deserialize(dict(row)) if row else None


async def delete_setting(conn: asyncpg.Connection, *, company_id: str, key: str) -> bool:
    result = await conn.execute(
        "DELETE FROM settings WHERE company_id = $1 AND key = $2",
        company_id,
        key,
    )
    deleted: int = 1 if result.endswith("1") else 0
    return bool(deleted)


async def list_settings(conn: asyncpg.Connection, *, company_id: str) -> dict[str, Any]:
    rows = await conn.fetch("SELECT key, value FROM settings WHERE company_id = $1", company_id)
    return {row["key"]: _decode(row["value"]) for row in rows}

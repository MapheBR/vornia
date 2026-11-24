"""Repositório de refresh tokens (somente role de bootstrap)."""

from datetime import datetime
from typing import Any

import asyncpg


async def create_refresh_token(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    company_id: str,
    token_hash: str,
    family_id: str,
    expires_at: datetime,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        INSERT INTO refresh_tokens
            (user_id, company_id, token_hash, family_id, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, user_id, company_id, family_id, expires_at, created_at
        """,
        user_id,
        company_id,
        token_hash,
        family_id,
        expires_at,
    )
    return dict(row) if row else None


async def get_by_hash(conn: asyncpg.Connection, token_hash: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        SELECT id, user_id, company_id, family_id, expires_at, revoked_at, replaced_by_id
        FROM refresh_tokens
        WHERE token_hash = $1
        """,
        token_hash,
    )
    return dict(row) if row else None


async def revoke_token(
    conn: asyncpg.Connection,
    *,
    token_id: str,
    replaced_by_id: str | None,
) -> None:
    await conn.execute(
        """
        UPDATE refresh_tokens
        SET revoked_at = now(), replaced_by_id = $2
        WHERE id = $1
        """,
        token_id,
        replaced_by_id,
    )


async def revoke_family(conn: asyncpg.Connection, *, family_id: str) -> None:
    """Revoga toda a família em caso de reuso detectado."""
    await conn.execute(
        "UPDATE refresh_tokens SET revoked_at = now() WHERE family_id = $1 AND revoked_at IS NULL",
        family_id,
    )

"""Auth repository."""

from typing import Any

import asyncpg


async def create_company(conn: asyncpg.Connection, name: str, slug: str) -> dict[str, Any]:
    row = await conn.fetchrow(
        "INSERT INTO companies (name, slug) VALUES ($1, $2) RETURNING id, name, slug, created_at",
        name,
        slug,
    )
    return dict(row) if row else {}


async def create_user(
    conn: asyncpg.Connection,
    *,
    email: str,
    password_hash: str,
    full_name: str,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        "INSERT INTO users (email, password_hash, full_name) VALUES ($1, $2, $3) RETURNING id, email, full_name, is_active, created_at",
        email,
        password_hash,
        full_name,
    )
    return dict(row) if row else {}


async def create_company_user(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    user_id: str,
    role: str,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        "INSERT INTO company_users (company_id, user_id, role) VALUES ($1, $2, $3) RETURNING id, company_id, user_id, role, created_at",
        company_id,
        user_id,
        role,
    )
    return dict(row) if row else {}


async def get_user_by_email(conn: asyncpg.Connection, email: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT id, email, password_hash, full_name, is_active FROM users WHERE email = $1",
        email,
    )
    return dict(row) if row else None


async def get_user_by_id(conn: asyncpg.Connection, user_id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT id, email, full_name FROM users WHERE id = $1",
        user_id,
    )
    return dict(row) if row else None


async def get_company_user(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT company_id, role FROM company_users WHERE user_id = $1",
        user_id,
    )
    return dict(row) if row else None

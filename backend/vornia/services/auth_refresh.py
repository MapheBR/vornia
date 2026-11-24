"""Fluxo de refresh/logout de tokens (somente via bootstrap_connection)."""

from typing import Any

from vornia.middleware.rls import bootstrap_connection
from vornia.repositories import token as token_repo
from vornia.repositories.auth import get_company_user, get_user_by_id
from vornia.services.token import (
    detect_reuse,
    generate_refresh_token,
    hash_token,
    refresh_expiry,
)


async def issue_refresh_token(
    conn: Any,
    *,
    user_id: str,
    company_id: str,
    family_id: str | None = None,
) -> str:
    """Cria um refresh token, opcionalmente dentro de uma família existente."""
    import uuid

    token = generate_refresh_token()
    await token_repo.create_refresh_token(
        conn,
        user_id=user_id,
        company_id=company_id,
        token_hash=hash_token(token),
        family_id=family_id or str(uuid.uuid4()),
        expires_at=refresh_expiry(),
    )
    return token


async def refresh_session(*, refresh_token: str) -> dict[str, Any]:
    """Rotaciona o refresh token; reuso revoga a família inteira."""
    token_hash = hash_token(refresh_token)
    async with bootstrap_connection() as conn:
        row = await token_repo.get_by_hash(conn, token_hash)

        if row is None:
            raise ValueError("Invalid refresh token")

        if detect_reuse(row):
            await token_repo.revoke_family(conn, family_id=str(row["family_id"]))
            raise ValueError("Refresh token reuse detected")

        if row["revoked_at"] is not None:
            raise ValueError("Invalid refresh token")

        from datetime import UTC, datetime

        expires_at = row["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            raise ValueError("Refresh token expired")

        user = await get_user_by_id(conn, str(row["user_id"]))
        company_user = await get_company_user(conn, str(row["user_id"]))
        if user is None or company_user is None:
            raise ValueError("Invalid refresh token")

        new_token = await issue_refresh_token(
            conn,
            user_id=str(row["user_id"]),
            company_id=str(row["company_id"]),
            family_id=str(row["family_id"]),
        )
        new_row = await token_repo.get_by_hash(conn, hash_token(new_token))
        await token_repo.revoke_token(
            conn,
            token_id=str(row["id"]),
            replaced_by_id=str(new_row["id"]) if new_row else None,
        )

        from vornia.services.security import create_access_token

        access = create_access_token(
            user_id=str(row["user_id"]),
            email=user["email"],
            company_id=str(row["company_id"]),
            role=company_user["role"],
        )

    return {
        "token": access,
        "refresh_token": new_token,
        "id": str(row["user_id"]),
        "email": user["email"],
        "company_id": str(row["company_id"]),
        "role": company_user["role"],
    }


async def revoke_refresh_session(*, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    async with bootstrap_connection() as conn:
        row = await token_repo.get_by_hash(conn, token_hash)
        if row is not None:
            await token_repo.revoke_token(conn, token_id=str(row["id"]), replaced_by_id=None)

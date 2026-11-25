"""Serviço de settings com defaults e isolamento por tenant."""

from typing import Any

from vornia.middleware.rls import rls_connection
from vornia.repositories import settings as settings_repo
from vornia.services.settings_registry import (
    DEFAULTS,
    default_for,
    validate_setting,
)


def effective(overrides: dict[str, Any]) -> dict[str, Any]:
    """Defaults mesclados com sobrescritas persistidas."""
    return {**DEFAULTS, **overrides}


async def list_effective(*, company_id: str) -> dict[str, Any]:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        overrides = await settings_repo.list_settings(conn, company_id=company_id)
    return effective(overrides)


async def get_effective(*, company_id: str, key: str) -> dict[str, Any]:
    default = default_for(key)
    async with rls_connection(claims={"company_id": company_id}) as conn:
        row = await settings_repo.get_setting(conn, company_id=company_id, key=key)
    return {"key": key, "value": row["value"] if row else default}


async def upsert(*, company_id: str, key: str, payload: dict[str, Any]) -> dict[str, Any]:
    value = validate_setting(key, payload)
    async with rls_connection(claims={"company_id": company_id}) as conn:
        row = await settings_repo.upsert_setting(conn, company_id=company_id, key=key, value=value)
    return {"key": key, "value": value, "updated_at": row.get("updated_at") if row else None}


async def remove(*, company_id: str, key: str) -> None:
    default_for(key)
    async with rls_connection(claims={"company_id": company_id}) as conn:
        await settings_repo.delete_setting(conn, company_id=company_id, key=key)

"""Company settings service — every query runs inside an RLS-scoped transaction."""

import json
from typing import Any

from vornia.middleware.rls import rls_connection
from vornia.repositories import settings as settings_repo


def _claims(company_id: str) -> dict[str, str]:
    return {"company_id": company_id}


def _decode_value(value: Any) -> Any:
    """asyncpg devolve JSONB como texto JSON; decodifica para o valor original."""
    return json.loads(value) if isinstance(value, str) else value


def _serialize(record: dict[str, Any]) -> dict[str, Any]:
    """Normaliza UUIDs e JSONB antes da validação do response model."""
    return {
        **record,
        "id": str(record["id"]),
        "company_id": str(record["company_id"]),
        "value": _decode_value(record["value"]),
    }


async def list_all(*, company_id: str) -> dict[str, Any]:
    async with rls_connection(claims=_claims(company_id)) as conn:
        settings = await settings_repo.list_all(conn)
    return {key: _decode_value(value) for key, value in settings.items()}


async def get(*, company_id: str, key: str) -> dict[str, Any] | None:
    async with rls_connection(claims=_claims(company_id)) as conn:
        setting = await settings_repo.get_by_key(conn, key)
        return _serialize(setting) if setting else None


async def upsert(*, company_id: str, key: str, value: Any) -> dict[str, Any]:
    async with rls_connection(claims=_claims(company_id)) as conn:
        return _serialize(
            await settings_repo.upsert(conn, company_id=company_id, key=key, value=value)
        )


async def delete(*, company_id: str, key: str) -> bool:
    async with rls_connection(claims=_claims(company_id)) as conn:
        return await settings_repo.delete(conn, key)

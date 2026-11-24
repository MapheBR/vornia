"""Employee service — every query runs inside an RLS-scoped transaction."""

from typing import Any

from vornia.middleware.rls import rls_connection
from vornia.repositories import employees as employees_repo


def _claims(company_id: str) -> dict[str, str]:
    return {"company_id": company_id}


def _serialize(record: dict[str, Any]) -> dict[str, Any]:
    """Converte UUIDs do asyncpg para strings antes da validação do response model."""
    return {
        **record,
        "id": str(record["id"]),
        "company_id": str(record["company_id"]),
    }


async def create(*, company_id: str, data: dict[str, Any]) -> dict[str, Any]:
    async with rls_connection(claims=_claims(company_id)) as conn:
        return _serialize(await employees_repo.create(conn, company_id=company_id, data=data))


async def list_all(*, company_id: str) -> list[dict[str, Any]]:
    async with rls_connection(claims=_claims(company_id)) as conn:
        return [_serialize(row) for row in await employees_repo.list_all(conn)]


async def get(*, company_id: str, employee_id: str) -> dict[str, Any] | None:
    async with rls_connection(claims=_claims(company_id)) as conn:
        employee = await employees_repo.get_by_id(conn, employee_id)
        return _serialize(employee) if employee else None


async def update(
    *,
    company_id: str,
    employee_id: str,
    changes: dict[str, Any],
) -> dict[str, Any] | None:
    async with rls_connection(claims=_claims(company_id)) as conn:
        employee = await employees_repo.update(conn, employee_id=employee_id, changes=changes)
        return _serialize(employee) if employee else None


async def delete(*, company_id: str, employee_id: str) -> bool:
    async with rls_connection(claims=_claims(company_id)) as conn:
        return await employees_repo.soft_delete(conn, employee_id)

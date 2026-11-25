"""Employee service (with tenant isolation by RLS)."""

from typing import Any

from vornia.middleware.rls import rls_connection
from vornia.repositories import employee as employee_repo
from vornia.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    mask_for_role,
)


def _to_response(row: dict[str, Any], *, show_cpf: bool) -> EmployeeResponse:
    data = dict(row)
    data["id"] = str(data["id"])
    if not show_cpf:
        data["cpf"] = None
    return EmployeeResponse(**data)


async def create_employee(
    *,
    company_id: str,
    data: EmployeeCreate,
) -> EmployeeResponse:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        row = await employee_repo.create_employee(conn, company_id=company_id, data=data)
    if row is None:
        raise ValueError("Falha ao criar colaborador")
    return _to_response(row, show_cpf=True)


async def get_employee(
    *,
    company_id: str,
    employee_id: str,
) -> EmployeeResponse:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        row = await employee_repo.get_employee(conn, employee_id)
    if row is None or row.get("is_active") is False:
        raise LookupError("Colaborador não encontrado")
    return _to_response(row, show_cpf=True)


async def update_employee(
    *,
    company_id: str,
    employee_id: str,
    data: EmployeeUpdate,
    role: str,
) -> EmployeeResponse:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        row = await employee_repo.update_employee(conn, employee_id=employee_id, data=data)
    if row is None:
        raise LookupError("Colaborador não encontrado")
    return _to_response(row, show_cpf=mask_for_role(role))


async def deactivate_employee(*, company_id: str, employee_id: str) -> None:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        found = await employee_repo.deactivate_employee(conn, employee_id=employee_id)
    if not found:
        raise LookupError("Colaborador não encontrado")


async def list_employees(
    *,
    company_id: str,
    page: int = 1,
    per_page: int = 20,
    active: bool | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        rows, total = await employee_repo.list_employees(
            conn,
            company_id=company_id,
            page=page,
            per_page=per_page,
            active=active,
            search=search,
        )
    total_pages = (total + per_page - 1) // per_page
    return {
        "data": [_to_response(row, show_cpf=False) for row in rows],
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    }

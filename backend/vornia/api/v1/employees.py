"""Employee API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from vornia.dependencies import get_tenant_user
from vornia.schemas.employees import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from vornia.services import employees as employees_service

router = APIRouter(tags=["employees"])


def _tenant_id(current_user: dict[str, Any]) -> str:
    return str(current_user["company_id"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EmployeeResponse,
)
async def create_employee(
    request: EmployeeCreate,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> dict[str, Any]:
    return await employees_service.create(
        company_id=_tenant_id(current_user),
        data=request.model_dump(),
    )


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> list[dict[str, Any]]:
    return await employees_service.list_all(company_id=_tenant_id(current_user))


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> dict[str, Any]:
    employee = await employees_service.get(
        company_id=_tenant_id(current_user),
        employee_id=employee_id,
    )
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    request: EmployeeUpdate,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> dict[str, Any]:
    employee = await employees_service.update(
        company_id=_tenant_id(current_user),
        employee_id=employee_id,
        changes=request.model_dump(exclude_unset=True),
    )
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> Response:
    deleted = await employees_service.delete(
        company_id=_tenant_id(current_user),
        employee_id=employee_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

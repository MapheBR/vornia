"""Employees API routes."""

from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from vornia.dependencies import get_current_user
from vornia.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from vornia.services import employee as employee_service

router = APIRouter(tags=["employees"], prefix="/employees")


def _current_user(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    return current_user


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EmployeeResponse,
    name="create_employee",
)
async def create_employee(
    data: EmployeeCreate,
    current_user: dict[str, Any] = Depends(_current_user),  # noqa: B008
) -> EmployeeResponse:
    try:
        return await employee_service.create_employee(
            company_id=current_user["company_id"],
            data=data,
        )
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já cadastrado para esta empresa",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=dict[str, Any], name="list_employees")
async def list_employees(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active: bool | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=100),
    current_user: dict[str, Any] = Depends(_current_user),  # noqa: B008
) -> dict[str, Any]:
    return await employee_service.list_employees(
        company_id=current_user["company_id"],
        page=page,
        per_page=per_page,
        active=active,
        search=search,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse, name="get_employee")
async def get_employee(
    employee_id: str,
    current_user: dict[str, Any] = Depends(_current_user),  # noqa: B008
) -> EmployeeResponse:
    try:
        return await employee_service.get_employee(
            company_id=current_user["company_id"],
            employee_id=employee_id,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Colaborador não encontrado",
        ) from exc


@router.patch("/{employee_id}", response_model=EmployeeResponse, name="update_employee")
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    current_user: dict[str, Any] = Depends(_current_user),  # noqa: B008
) -> EmployeeResponse:
    try:
        return await employee_service.update_employee(
            company_id=current_user["company_id"],
            employee_id=employee_id,
            data=data,
            role=current_user["role"],
        )
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já cadastrado para esta empresa",
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Colaborador não encontrado",
        ) from exc


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, name="deactivate_employee")
async def deactivate_employee(
    employee_id: str,
    current_user: dict[str, Any] = Depends(_current_user),  # noqa: B008
) -> None:
    try:
        await employee_service.deactivate_employee(
            company_id=current_user["company_id"],
            employee_id=employee_id,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Colaborador não encontrado",
        ) from exc

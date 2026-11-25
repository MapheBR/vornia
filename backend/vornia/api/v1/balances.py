"""Endpoints de banco de horas e feriados."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from vornia.dependencies import get_current_user
from vornia.middleware.rls import rls_connection
from vornia.services import balance_service

router = APIRouter(tags=["balances"])


@router.post("/balances/recalculate")
async def recalculate(
    payload: dict[str, Any] | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, int]:
    month = str((payload or {}).get("month", "2026-11"))
    return await balance_service.recalculate_month(
        company_id=current_user["company_id"], month=month
    )


@router.get("/balances")
async def list_balances(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    return {
        "data": await balance_service.list_balances(
            company_id=current_user["company_id"]
        )
    }


@router.post("/holidays", status_code=status.HTTP_201_CREATED)
async def create_holiday(
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    from datetime import date as _date
    holiday_date = _date.fromisoformat(str(payload["date"]))

    async with rls_connection(claims={"company_id": current_user["company_id"]}) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO holidays (company_id, date, name, jornada_especial_hours)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (company_id, date) DO UPDATE SET name = EXCLUDED.name
            RETURNING date, name, jornada_especial_hours
            """,
            current_user["company_id"],
            holiday_date,
            payload["name"],
            payload.get("jornada_especial_hours", 4.0),
        )
    return dict(row) if row else {}


@router.get("/holidays")
async def list_holidays(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    async with rls_connection(claims={"company_id": current_user["company_id"]}) as conn:
        rows = await conn.fetch(
            "SELECT date, name, jornada_especial_hours FROM holidays WHERE company_id = $1",
            current_user["company_id"],
        )
    return {"data": [dict(row) for row in rows]}

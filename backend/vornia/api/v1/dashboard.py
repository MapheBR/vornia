"""Endpoints de dashboard: agregações por tenant via RLS."""

from typing import Any

from fastapi import APIRouter, Depends

from vornia.dependencies import get_current_user
from vornia.middleware.rls import rls_connection

router = APIRouter(tags=["dashboard"], prefix="/dashboard")


@router.get("/summary")
async def summary(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    company_id = current_user["company_id"]
    async with rls_connection(claims={"company_id": company_id}) as conn:
        total = await conn.fetchval(
            "SELECT count(*) FROM employees WHERE company_id = $1", company_id
        )
        worked = await conn.fetchval(
            """
            SELECT COALESCE(sum(worked_hours), 0) FROM processed_journeys WHERE company_id = $1
            """,
            company_id,
        )
        inconsistent = await conn.fetchval(
            """
            SELECT count(*) FROM processed_journeys
            WHERE company_id = $1 AND status = 'inconsistency'
            """,
            company_id,
        )
        pending = await conn.fetchval(
            """
            SELECT count(*) FROM processed_journeys
            WHERE company_id = $1 AND status = 'pending'
            """,
            company_id,
        )
    return {
        "total_employees": int(total or 0),
        "hours_worked": float(worked or 0),
        "inconsistencies": int(inconsistent or 0),
        "pending_journeys": int(pending or 0),
    }


@router.get("/inconsistencies")
async def inconsistencies(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    company_id = current_user["company_id"]
    async with rls_connection(claims={"company_id": company_id}) as conn:
        rows = await conn.fetch(
            """
            SELECT id, employee_id, date, worked_hours, expected_hours, status, notes
            FROM processed_journeys
            WHERE company_id = $1 AND status IN ('inconsistency','pending')
            ORDER BY date DESC
            LIMIT 100
            """,
            company_id,
        )
    return {"data": [dict(row) for row in rows]}

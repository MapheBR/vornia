"""Endpoints de exportação de jornadas (XLSX/PDF)."""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from vornia.dependencies import get_current_user
from vornia.middleware.rls import rls_connection
from vornia.services.exports import PDF_ROW_LIMIT, XLSX_ROW_LIMIT, build_pdf, build_xlsx

router = APIRouter(tags=["exports"], prefix="/exports")


async def _fetch(
    *,
    company_id: str,
    employee_id: UUID | None,
    start: date,
    end: date,
    limit: int,
) -> list[dict[str, Any]]:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, e.name AS employee, p.date, p.entry, p.exit,
                   p.worked_hours, p.status
            FROM processed_journeys p
            JOIN employees e ON e.id = p.employee_id
            WHERE p.company_id = $1 AND p.date BETWEEN $2 AND $3
              AND ($4::uuid IS NULL OR p.employee_id = $4)
            ORDER BY p.date DESC
            LIMIT $5
            """,
            company_id,
            start,
            end,
            employee_id,
            limit,
        )
    return [dict(row) for row in rows]


@router.get("/journeys.xlsx")
async def export_xlsx(
    start: date = Query(...),  # noqa: B008
    end: date = Query(...),  # noqa: B008
    employee_id: UUID | None = Query(None),  # noqa: B008
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> Response:
    if end < start or end - start > timedelta(days=366):
        raise HTTPException(422, detail="Intervalo inválido (máx. 366 dias)")
    rows = await _fetch(
        company_id=current_user["company_id"],
        employee_id=employee_id,
        start=start,
        end=end,
        limit=XLSX_ROW_LIMIT + 1,
    )
    if len(rows) > XLSX_ROW_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas linhas",
            headers={"Retry-After": "60"},
        )
    return Response(
        content=build_xlsx(rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="jornadas.xlsx"'},
    )


@router.get("/journeys.pdf")
async def export_pdf(
    start: date = Query(...),  # noqa: B008
    end: date = Query(...),  # noqa: B008
    employee_id: UUID | None = Query(None),  # noqa: B008
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> Response:
    if end < start or end - start > timedelta(days=366):
        raise HTTPException(422, detail="Intervalo inválido (máx. 366 dias)")
    rows = await _fetch(
        company_id=current_user["company_id"],
        employee_id=employee_id,
        start=start,
        end=end,
        limit=PDF_ROW_LIMIT + 1,
    )
    if len(rows) > PDF_ROW_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite de {PDF_ROW_LIMIT} linhas",
            headers={"Retry-After": "60"},
        )
    return Response(
        content=build_pdf(rows),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="jornadas.pdf"'},
    )

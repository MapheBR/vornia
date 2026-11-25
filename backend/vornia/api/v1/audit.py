"""Endpoints de edição manual e consulta de auditoria."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from vornia.dependencies import get_current_user
from vornia.middleware.rls import rls_connection
from vornia.services import manual_edit

router = APIRouter(tags=["audit"])


@router.patch("/raw-punches/{punch_id}")
async def edit_punch(
    punch_id: UUID,
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    reason = str(payload.get("reason", ""))
    punched_at = payload.get("punched_at")
    if punched_at is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="punched_at obrigatório"
        )
    try:
        return await manual_edit.edit_punch(
            company_id=current_user["company_id"],
            punch_id=str(punch_id),
            punched_at=str(punched_at),
            reason=reason,
            changed_by=current_user["user_id"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=200),  # noqa: B008
    offset: int = Query(0, ge=0),  # noqa: B008
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    if current_user["role"] not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão")
    async with rls_connection(claims={"company_id": current_user["company_id"]}) as conn:
        rows = await conn.fetch(
            """
            SELECT id, entity_type, entity_id, action, changed_by, changed_at, reason
            FROM audit_logs WHERE company_id = $1 ORDER BY changed_at DESC
            LIMIT $2 OFFSET $3
            """,
            current_user["company_id"],
            limit,
            offset,
        )
    return {"data": [dict(row) for row in rows]}

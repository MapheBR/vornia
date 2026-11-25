"""Endpoints de sincronização Control iD."""

from typing import Any

from fastapi import APIRouter, Depends

from vornia.dependencies import get_current_user
from vornia.services import controlid_sync

router = APIRouter(tags=["sync"], prefix="/sync")


@router.post("/controlid")
async def sync_controlid(
    payload: dict[str, Any] | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, int]:
    return await controlid_sync.sync_company(
        company_id=current_user["company_id"],
        full=bool((payload or {}).get("full", False)),
    )


@router.get("/state")
async def sync_state(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    state = await controlid_sync.get_sync_state(company_id=current_user["company_id"])
    return {"data": state}

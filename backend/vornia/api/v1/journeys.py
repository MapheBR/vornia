"""Endpoint de processamento de jornadas."""

from typing import Any

from fastapi import APIRouter, Depends

from vornia.dependencies import get_current_user
from vornia.services import journey_processing

router = APIRouter(tags=["journeys"], prefix="/sync")


@router.post("/process")
async def process_journeys(
    payload: dict[str, Any] | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, int]:
    del payload
    return await journey_processing.process_company(company_id=current_user["company_id"])

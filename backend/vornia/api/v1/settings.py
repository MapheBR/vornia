"""Company settings API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from vornia.dependencies import get_tenant_user
from vornia.schemas.settings import SettingsResponse, SettingsUpdate
from vornia.services import settings as settings_service

router = APIRouter(tags=["settings"])


def _tenant_id(current_user: dict[str, Any]) -> str:
    return str(current_user["company_id"])


@router.get("")
async def list_settings(
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> dict[str, Any]:
    return await settings_service.list_all(company_id=_tenant_id(current_user))


@router.get("/{key}", response_model=SettingsResponse)
async def get_setting(
    key: str,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> dict[str, Any]:
    setting = await settings_service.get(company_id=_tenant_id(current_user), key=key)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return setting


@router.put("/{key}", response_model=SettingsResponse)
async def put_setting(
    key: str,
    request: SettingsUpdate,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> dict[str, Any]:
    return await settings_service.upsert(
        company_id=_tenant_id(current_user),
        key=key,
        value=request.value,
    )


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    current_user: dict[str, Any] = Depends(get_tenant_user),  # noqa: B008
) -> Response:
    deleted = await settings_service.delete(company_id=_tenant_id(current_user), key=key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

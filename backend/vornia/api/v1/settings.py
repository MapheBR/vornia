"""Settings API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from vornia.dependencies import get_current_user
from vornia.services import settings as settings_service

router = APIRouter(tags=["settings"], prefix="/settings")


def _tenant(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> str:
    company_id: str = current_user["company_id"]
    return company_id


@router.get("", response_model=dict[str, Any])
async def list_settings(company_id: str = Depends(_tenant)) -> dict[str, Any]:  # noqa: B008
    return {"data": await settings_service.list_effective(company_id=company_id)}


@router.get("/{key}", response_model=dict[str, Any])
async def get_setting(
    key: str,
    company_id: str = Depends(_tenant),  # noqa: B008
) -> dict[str, Any]:
    try:
        return await settings_service.get_effective(company_id=company_id, key=key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chave desconhecida",
        ) from exc


@router.put("/{key}", response_model=dict[str, Any])
async def upsert_setting(
    key: str,
    payload: dict[str, Any],
    company_id: str = Depends(_tenant),  # noqa: B008
) -> dict[str, Any]:
    try:
        return await settings_service.upsert(company_id=company_id, key=key, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chave desconhecida",
        ) from exc
    except Exception as exc:
        from pydantic import ValidationError

        if isinstance(exc, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Valor inválido",
            ) from exc
        raise


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    company_id: str = Depends(_tenant),  # noqa: B008
) -> None:
    try:
        await settings_service.remove(company_id=company_id, key=key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chave desconhecida",
        ) from exc

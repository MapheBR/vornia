"""Auth API routes."""

from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from vornia.dependencies import get_current_user
from vornia.infrastructure.settings import settings
from vornia.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from vornia.services import auth as auth_service
from vornia.services.auth_refresh import refresh_session, revoke_refresh_session

router = APIRouter(tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=86400,
        path="/",
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,
        path="/api/v1/auth",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(request: RegisterRequest, response: Response) -> dict[str, Any]:
    try:
        result = await auth_service.register(
            company_name=request.company_name,
            email=str(request.email),
            password=request.password,
            full_name=request.full_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    _set_auth_cookie(response, result["token"])
    _set_refresh_cookie(response, result["refresh_token"])

    return {
        "id": result["id"],
        "email": result["email"],
        "full_name": result["full_name"],
        "company_id": result["company_id"],
        "role": result["role"],
    }


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest, response: Response) -> dict[str, Any]:
    try:
        result = await auth_service.login(
            email=str(request.email),
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc

    _set_auth_cookie(response, result["token"])
    _set_refresh_cookie(response, result["refresh_token"])

    return {
        "id": result["id"],
        "email": result["email"],
        "full_name": result["full_name"],
        "company_id": result["company_id"],
        "role": result["role"],
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
    try:
        return await auth_service.get_me(
            user_id=current_user["user_id"],
            company_id=current_user["company_id"],
            role=current_user["role"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for this tenant",
        ) from exc


@router.post("/refresh", response_model=UserResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None),
) -> dict[str, Any]:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    try:
        result = await refresh_session(refresh_token=refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    _set_auth_cookie(response, result["token"])
    _set_refresh_cookie(response, result["refresh_token"])
    return {
        "id": result["id"],
        "email": result["email"],
        "full_name": result["email"],
        "company_id": result["company_id"],
        "role": result["role"],
    }


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None),
) -> dict[str, Any]:
    if refresh_token is not None:
        await revoke_refresh_session(refresh_token=refresh_token)
    response.delete_cookie(
        key="token",
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )
    return {"message": "Logged out"}

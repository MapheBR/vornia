"""Auth API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from vornia.dependencies import get_current_user
from vornia.infrastructure.settings import settings
from vornia.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from vornia.services import auth as auth_service

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

    return {
        "id": result["id"],
        "email": result["email"],
        "full_name": result["full_name"],
        "company_id": result["company_id"],
        "role": result["role"],
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
    return await auth_service.get_me(
        user_id=current_user["user_id"],
        company_id=current_user["company_id"],
        role=current_user["role"],
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, Any]:
    response.delete_cookie(
        key="token",
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return {"message": "Logged out"}

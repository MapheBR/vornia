"""FastAPI dependencies."""

from typing import Any

import jwt
from fastapi import Cookie, Depends, HTTPException, status

from vornia.middleware.rls import bootstrap_connection
from vornia.services.security import decode_access_token


async def get_current_user(token: str | None = Cookie(None)) -> dict[str, Any]:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "company_id": payload["company_id"],
        "role": payload["role"],
    }


async def get_tenant_user(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    """Exige que o usuario pertença de fato ao tenant declarado no JWT.

    O RLS isola as linhas pela claim, mas nao verifica o vinculo do usuario com a
    empresa. Sem esta checagem, um token com company_id divergente tera acesso
    aos dados daquele tenant (defesa em profundidade).
    """
    async with bootstrap_connection() as conn:
        membership = await conn.fetchrow(
            """
            SELECT 1 FROM company_users
            WHERE user_id = $1 AND company_id = $2
            """,
            current_user["user_id"],
            current_user["company_id"],
        )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized for this tenant",
        )

    return current_user

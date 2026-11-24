"""Auth service."""

import re
from typing import Any

from vornia.middleware.rls import bootstrap_connection, rls_connection
from vornia.repositories import auth as auth_repo
from vornia.services.security import create_access_token, hash_password, verify_password


async def register(
    *,
    company_name: str,
    email: str,
    password: str,
    full_name: str,
) -> dict[str, Any]:
    slug = _slugify(company_name)
    password_hash = hash_password(password)

    async with bootstrap_connection() as conn:
        company = await auth_repo.create_company(conn, company_name, slug)
        company_id = str(company["id"])

        user = await auth_repo.create_user(
            conn,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        user_id = str(user["id"])

        await auth_repo.create_company_user(
            conn,
            company_id=company_id,
            user_id=user_id,
            role="admin",
        )

        token = create_access_token(
            user_id=user_id,
            email=email,
            company_id=company_id,
            role="admin",
        )

    return {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "company_id": company_id,
        "role": "admin",
        "token": token,
    }


async def login(*, email: str, password: str) -> dict[str, Any]:
    async with bootstrap_connection() as conn:
        user = await auth_repo.get_user_by_email(conn, email)

        if user is None or not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid credentials")

        user_id = str(user["id"])
        company_user = await auth_repo.get_company_user(conn, user_id)

        if company_user is None:
            raise ValueError("User is not associated with any company")

        company_id = str(company_user["company_id"])
        role = company_user["role"]

        token = create_access_token(
            user_id=user_id,
            email=email,
            company_id=company_id,
            role=role,
        )

    return {
        "id": user_id,
        "email": email,
        "full_name": user["full_name"],
        "company_id": company_id,
        "role": role,
        "token": token,
    }


async def get_me(*, user_id: str, company_id: str, role: str) -> dict[str, Any]:
    async with rls_connection(claims={"company_id": company_id}) as conn:
        user = await auth_repo.get_user_by_id(conn, user_id)

        if user is None:
            raise ValueError("User not found")

    return {
        "id": str(user["id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "company_id": company_id,
        "role": role,
    }


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    return value[:100]

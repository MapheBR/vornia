"""Employee CRUD integration tests, including tenant isolation."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from vornia.main import app
from vornia.services.security import create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _register_company(name: str, email: str) -> tuple[AsyncClient, dict[str, Any]]:
    """Create a tenant and return an authenticated client plus its registration data."""
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": name,
            "email": email,
            "password": "strong-password",
            "full_name": "Admin",
        },
    )
    assert response.status_code == 201
    return client, response.json()


async def _create_employee(
    client: AsyncClient,
    name: str,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, **extra}
    response = await client.post("/api/v1/employees", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_employee_returns_201_with_tenant_id() -> None:
    client, registration = await _register_company("Acme", "admin@acme.example.com")
    try:
        employee = await _create_employee(
            client,
            "Maria da Silva",
            control_id=42,
            registration="A-100",
            department="TI",
            hired_at="2026-01-15",
        )

        assert employee["name"] == "Maria da Silva"
        assert employee["control_id"] == 42
        assert employee["registration"] == "A-100"
        assert employee["department"] == "TI"
        assert employee["hired_at"] == "2026-01-15"
        assert employee["company_id"] == registration["company_id"]
        assert employee["is_active"] is True
        assert "id" in employee
        assert "created_at" in employee
    finally:
        await client.aclose()


async def test_list_employees_returns_only_current_tenant() -> None:
    client_a, _ = await _register_company("Company A", "admin-a@example.com")
    client_b, _ = await _register_company("Company B", "admin-b@example.com")
    try:
        await _create_employee(client_a, "Employee A")
        await _create_employee(client_b, "Employee B")

        response = await client_a.get("/api/v1/employees")

        assert response.status_code == 200
        names = [employee["name"] for employee in response.json()]
        assert names == ["Employee A"]
    finally:
        await client_a.aclose()
        await client_b.aclose()


async def test_get_employee_by_id() -> None:
    client, _ = await _register_company("Acme", "admin@example.com")
    try:
        created = await _create_employee(client, "Maria")

        response = await client.get(f"/api/v1/employees/{created['id']}")

        assert response.status_code == 200
        assert response.json()["name"] == "Maria"
    finally:
        await client.aclose()


async def test_get_unknown_employee_returns_404() -> None:
    client, _ = await _register_company("Acme", "admin@example.com")
    try:
        response = await client.get("/api/v1/employees/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
    finally:
        await client.aclose()


async def test_patch_employee_updates_fields() -> None:
    client, _ = await _register_company("Acme", "admin@example.com")
    try:
        created = await _create_employee(client, "Maria", department="TI")

        response = await client.patch(
            f"/api/v1/employees/{created['id']}",
            json={"job_title": "Analista", "department": "RH"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_title"] == "Analista"
        assert data["department"] == "RH"
        assert data["name"] == "Maria"
    finally:
        await client.aclose()


async def test_delete_employee_soft_deletes() -> None:
    client, _ = await _register_company("Acme", "admin@example.com")
    try:
        created = await _create_employee(client, "Maria")

        response = await client.delete(f"/api/v1/employees/{created['id']}")

        assert response.status_code == 204
        get_response = await client.get(f"/api/v1/employees/{created['id']}")
        assert get_response.status_code == 404
        list_response = await client.get("/api/v1/employees")
        assert list_response.json() == []
    finally:
        await client.aclose()


async def test_employees_require_authentication() -> None:
    client, _ = await _register_company("Acme", "admin@example.com")
    try:
        client.cookies.clear()

        response = await client.get("/api/v1/employees")

        assert response.status_code == 401
    finally:
        await client.aclose()


async def test_forged_token_with_foreign_company_is_rejected() -> None:
    """Token com company_id divergente do vinculo real do usuario deve ser negado.

    RLS sozinho nao basta: a claim definiria o tenant B. A checagem de vinculo
    em get_tenant_user garante defesa em profundidade.
    """
    client_a, registration_a = await _register_company("Company A", "admin-a@example.com")
    client_b, registration_b = await _register_company("Company B", "admin-b@example.com")
    try:
        await _create_employee(client_a, "Secret Employee A")
        await _create_employee(client_b, "Employee B")

        forged_token = create_access_token(
            user_id=registration_a["id"],
            email="admin-a@example.com",
            company_id=registration_b["company_id"],
            role="admin",
        )
        client_a.cookies.set("token", forged_token)

        response = await client_a.get("/api/v1/employees")

        assert response.status_code == 401
    finally:
        await client_a.aclose()
        await client_b.aclose()

"""Integration tests for the employees CRUD API (with real PostgreSQL)."""

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from vornia.main import app

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

VALID_CPF_A = "52601815906"
VALID_PIS = "18609139092"

BASE_URL = "http://test"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL)


async def _register(client: AsyncClient, company_name: str, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": company_name,
            "email": email,
            "password": "strong-password",
            "full_name": "Admin",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


async def _login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password"},
    )
    assert response.status_code == status.HTTP_200_OK


def _employee_payload(**overrides):
    payload = {"name": "Colaborador"}
    payload.update(overrides)
    return payload


async def test_create_employee_returns_201(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    response = await client.post("/api/v1/employees", json=_employee_payload(cpf=VALID_CPF_A))
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Colaborador"
    assert data["cpf"] == VALID_CPF_A  # admin sees full CPF


async def test_list_employees_returns_pagination(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    for index in range(3):
        await client.post("/api/v1/employees", json=_employee_payload(name=f"Colaborador {index}"))
    response = await client.get("/api/v1/employees")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["meta"]["total"] == 3
    assert data["meta"]["page"] == 1
    assert data["meta"]["per_page"] == 20
    assert data["meta"]["total_pages"] == 1
    assert len(data["data"]) == 3


async def test_list_employees_pagination_and_filters(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    for index in range(5):
        await client.post("/api/v1/employees", json=_employee_payload(name=f"Colaborador {index}"))
    page_two = await client.get("/api/v1/employees", params={"page": 2, "per_page": 2})
    assert page_two.status_code == status.HTTP_200_OK
    assert page_two.json()["meta"]["page"] == 2

    by_name = await client.get("/api/v1/employees", params={"search": "Colaborador 3"})
    assert by_name.json()["meta"]["total"] == 1

    inactive = await client.post("/api/v1/employees", json=_employee_payload(name="Inativo"))
    assert inactive.status_code == status.HTTP_201_CREATED
    employee_id = inactive.json()["id"]
    assert (await client.delete(f"/api/v1/employees/{employee_id}")).status_code == 204
    inactive_filter = await client.get("/api/v1/employees", params={"active": False})
    assert inactive_filter.json()["meta"]["total"] == 1


async def test_get_employee_by_id(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    create = await client.post("/api/v1/employees", json=_employee_payload())
    employee_id = create.json()["id"]
    response = await client.get(f"/api/v1/employees/{employee_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == employee_id


async def test_get_employee_from_other_tenant_returns_404(
    client: AsyncClient, other_client: AsyncClient
) -> None:
    await _register(other_client, "Company B", "admin-b@acme.example.com")
    await _login(other_client, "admin-b@acme.example.com")
    create = await other_client.post("/api/v1/employees", json=_employee_payload())
    employee_id = create.json()["id"]

    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    response = await client.get(f"/api/v1/employees/{employee_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_employee_partial(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    create = await client.post("/api/v1/employees", json=_employee_payload())
    employee_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/employees/{employee_id}", json={"department": "RH", "name": "Rito N."}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["department"] == "RH"

    not_found = await client.patch(
        "/api/v1/employees/00000000-0000-4000-8000-000000000000", json={"name": "x"}
    )
    assert not_found.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_is_soft_delete(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    create = await client.post("/api/v1/employees", json=_employee_payload())
    employee_id = create.json()["id"]

    assert (await client.delete(f"/api/v1/employees/{employee_id}")).status_code == 204
    deleted = await client.get(f"/api/v1/employees/{employee_id}")
    assert deleted.status_code == status.HTTP_404_NOT_FOUND


async def test_invalid_cpf_rejected_by_api(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    response = await client.post("/api/v1/employees", json=_employee_payload(cpf="123"))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_duplicate_cpf_within_tenant_rejected(client: AsyncClient) -> None:
    await _register(client, "Company A", "admin-a@acme.example.com")
    await _login(client, "admin-a@acme.example.com")
    await client.post("/api/v1/employees", json=_employee_payload(cpf=VALID_CPF_A))
    duplicate = await client.post("/api/v1/employees", json=_employee_payload(cpf=VALID_CPF_A))
    assert duplicate.status_code == status.HTTP_409_CONFLICT

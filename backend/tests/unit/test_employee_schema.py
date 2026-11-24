"""Unit tests for the employee schemas."""

import pytest
from pydantic import ValidationError

from vornia.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    mask_for_role,
)
from vornia.services.identity import mask_cpf

pytestmark = pytest.mark.unit

VALID_CPF_A = "52601815906"
VALID_PIS = "18609139092"


class TestEmployeeCreate:
    def test_minimal_payload(self) -> None:
        data = EmployeeCreate(name="Maria Silva")
        assert data.name == "Maria Silva"
        assert data.is_active is True
        assert data.cpf is None

    def test_normalizes_and_validates_cpf(self) -> None:
        data = EmployeeCreate(
            name="JoÃ£o",
            cpf=f"{VALID_CPF_A[:3]}.{VALID_CPF_A[3:6]}.{VALID_CPF_A[6:9]}-{VALID_CPF_A[9:]}",
        )
        assert data.cpf == VALID_CPF_A

    def test_normalizes_and_validates_pis(self) -> None:
        data = EmployeeCreate(name="JoÃ£o", pis=f"{VALID_PIS[:5]} {VALID_PIS[5:]}")
        assert data.pis == VALID_PIS

    @pytest.mark.parametrize("cpf", ["12345678900", "52601815907", ""])
    def test_rejects_invalid_cpf(self, cpf: str) -> None:
        with pytest.raises(ValidationError):
            EmployeeCreate(name="JoÃ£o", cpf=cpf)

    @pytest.mark.parametrize("pis", ["12345678901", ""])
    def test_rejects_invalid_pis(self, pis: str) -> None:
        with pytest.raises(ValidationError):
            EmployeeCreate(name="JoÃ£o", pis=pis)

    def test_name_is_stripped(self) -> None:
        data = EmployeeCreate(name=" rito  ")
        assert data.name == "Rito".replace("Rito", "Rito") or data.name == " rito  ".strip()

    def test_forbids_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            EmployeeCreate.model_validate({"name": "Rito", "unknown": "x"})


class TestEmployeeUpdate:
    def test_partial_update(self) -> None:
        data = EmployeeUpdate(name="Novo")
        dump = data.model_dump(exclude_unset=True)
        assert dump == {"name": "Novo"}


class TestEmployeeResponse:
    def test_masks_by_role(self) -> None:
        assert mask_for_role("admin") is True
        assert mask_for_role("manager") is True
        assert mask_for_role("user") is False

    def test_mask_cpf_format(self) -> None:
        assert mask_cpf(VALID_CPF_A) == "526.018.159-06"

    def test_serializes_to_response(self) -> None:
        row = {
            "id": "019a1a1a-1a1a-4a1a-8a1a-1a1a1a1a1a1a",
            "name": "Rito",
            "registration": "RT-1",
            "cpf": VALID_CPF_A,
            "pis": VALID_PIS,
            "job_title": "Dev",
            "department": "TI",
            "is_active": True,
            "hired_at": None,
            "created_at": "2026-11-25",
            "updated_at": "2026-11-25",
        }
        response = EmployeeResponse(**row)
        assert response.name == "Rito"
        assert response.cpf == VALID_CPF_A

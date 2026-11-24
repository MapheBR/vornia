"""Unit tests for employee and settings schemas."""

from datetime import date

import pytest
from pydantic import ValidationError

from vornia.schemas.employees import EmployeeCreate, EmployeeUpdate
from vornia.schemas.settings import SettingsUpdate

pytestmark = pytest.mark.unit


def test_employee_create_accepts_minimal_payload() -> None:
    employee = EmployeeCreate(name="Maria da Silva")

    assert employee.name == "Maria da Silva"
    assert employee.control_id is None
    assert employee.is_active is True


def test_employee_create_accepts_full_payload() -> None:
    employee = EmployeeCreate(
        name="Maria da Silva",
        control_id=42,
        registration="A-100",
        pis="123.45678.90-1",
        cpf="123.456.789-00",
        job_title="Analista",
        department="TI",
        work_schedule={"seg": "08:00-17:00"},
        photo_url="https://example.com/photo.jpg",
        hired_at=date(2026, 1, 15),
        is_active=True,
    )

    assert employee.control_id == 42
    assert employee.job_title == "Analista"
    assert employee.hired_at == date(2026, 1, 15)
    assert employee.work_schedule == {"seg": "08:00-17:00"}


def test_employee_create_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        EmployeeCreate(name="")


def test_employee_create_rejects_name_longer_than_200_chars() -> None:
    with pytest.raises(ValidationError):
        EmployeeCreate(name="a" * 201)


def test_employee_create_rejects_negative_control_id() -> None:
    with pytest.raises(ValidationError):
        EmployeeCreate(name="Maria", control_id=-1)


def test_employee_update_leaves_all_fields_optional() -> None:
    update = EmployeeUpdate()

    assert update.name is None
    assert update.department is None
    assert update.model_dump(exclude_unset=True) == {}


def test_employee_update_rejects_empty_name_when_provided() -> None:
    with pytest.raises(ValidationError):
        EmployeeUpdate(name="")


def test_settings_update_accepts_any_json_value() -> None:
    assert SettingsUpdate(value={"timezone": "America/Sao_Paulo"}).value == {
        "timezone": "America/Sao_Paulo"
    }
    assert SettingsUpdate(value="texto").value == "texto"
    assert SettingsUpdate(value=42).value == 42

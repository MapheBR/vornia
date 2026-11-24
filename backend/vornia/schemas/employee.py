"""Schemas for employees (colaboradores)."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vornia.services.identity import is_valid_cpf, is_valid_pis, normalize_digits


class EmployeeCreate(BaseModel):
    """Payload de criacao de colaborador.

    Validadores normalizam CPF/PIS para apenas dígitos e rejeitam vazios.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    registration: str | None = Field(default=None, max_length=50)
    pis: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, max_length=20)
    job_title: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    work_schedule: dict[str, Any] | None = None
    photo_url: str | None = Field(default=None, max_length=2048)
    is_active: bool = True
    hired_at: date | None = None
    control_id: int | None = Field(default=None, ge=1)

    @field_validator("name", "job_title", "department", mode="before")
    def _strip_text(cls, value: str | None) -> str | None:  # noqa: N805
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("registration", "cpf", "pis", mode="before")
    def _normalize_ids(cls, value: str | None) -> str | None:  # noqa: N805
        if value is None:
            return None
        return normalize_digits(value.strip())

    @field_validator("cpf", mode="after")
    def _validate_cpf(cls, value: str | None) -> str | None:  # noqa: N805
        if value is not None and not is_valid_cpf(value):
            raise ValueError("CPF inválido")
        return value

    @field_validator("pis", mode="after")
    def _validate_pis(cls, value: str | None) -> str | None:  # noqa: N805
        if value is not None and not is_valid_pis(value):
            raise ValueError("PIS inválido")
        return value


class EmployeeUpdate(BaseModel):
    """Payload de atualização parcial; campos omitidos sao mantidos."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    registration: str | None = Field(default=None, max_length=50)
    pis: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, max_length=20)
    job_title: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    work_schedule: dict[str, Any] | None = None
    photo_url: str | None = Field(default=None, max_length=2048)
    is_active: bool | None = None
    hired_at: date | None = None
    control_id: int | None = Field(default=None, ge=1)

    @field_validator("name", "job_title", "department", mode="before")
    def _strip_text(cls, value: str | None) -> str | None:  # noqa: N805
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("registration", "cpf", "pis", mode="before")
    def _normalize_ids(cls, value: str | None) -> str | None:  # noqa: N805
        if value is None:
            return None
        return normalize_digits(value.strip())

    @field_validator("cpf", mode="after")
    def _validate_cpf(cls, value: str | None) -> str | None:  # noqa: N805
        if value is not None and not is_valid_cpf(value):
            raise ValueError("CPF inválido")
        return value

    @field_validator("pis", mode="after")
    def _validate_pis(cls, value: str | None) -> str | None:  # noqa: N805
        if value is not None and not is_valid_pis(value):
            raise ValueError("PIS inválido")
        return value


class EmployeeResponse(BaseModel):
    """Representacao de colaborador."""

    id: str
    name: str
    registration: str | None = None
    cpf: str | None = None
    pis: str | None = None
    job_title: str | None = None
    department: str | None = None
    is_active: bool = True
    hired_at: date | None = None
    created_at: datetime
    updated_at: datetime


def mask_for_role(role: str) -> bool:
    """Retorna True se o tom de voz tem direito ao CPF completo."""
    return role in ("admin", "manager")

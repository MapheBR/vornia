"""Employee schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    control_id: int | None = Field(default=None, ge=0)
    registration: str | None = Field(default=None, max_length=100)
    pis: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, max_length=20)
    job_title: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    work_schedule: dict[str, Any] | None = None
    photo_url: str | None = Field(default=None, max_length=500)
    hired_at: date | None = None
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    control_id: int | None = Field(default=None, ge=0)
    registration: str | None = Field(default=None, max_length=100)
    pis: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, max_length=20)
    job_title: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    work_schedule: dict[str, Any] | None = None
    photo_url: str | None = Field(default=None, max_length=500)
    hired_at: date | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: str
    company_id: str
    name: str
    control_id: int | None
    registration: str | None
    pis: str | None
    cpf: str | None
    job_title: str | None
    department: str | None
    work_schedule: dict[str, Any] | None
    photo_url: str | None
    is_active: bool
    hired_at: date | None
    created_at: datetime
    updated_at: datetime

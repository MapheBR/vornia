"""Company settings schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    value: Any = Field(..., description="JSON value stored for the setting")


class SettingsResponse(BaseModel):
    id: str
    company_id: str
    key: str
    value: Any
    created_at: datetime
    updated_at: datetime

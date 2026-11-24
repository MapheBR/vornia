"""Company model."""

from sqlalchemy import Column, DateTime, String, Table, func
from sqlalchemy.dialects.postgresql import UUID

from vornia.infrastructure.models.base import metadata

companies = Table(
    "companies",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("name", String(200), nullable=False),
    Column("slug", String(100), nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
)

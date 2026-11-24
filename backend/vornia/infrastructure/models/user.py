"""User model."""

from sqlalchemy import Boolean, Column, DateTime, String, Table, func
from sqlalchemy.dialects.postgresql import UUID

from vornia.infrastructure.models.base import metadata

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("full_name", String(200), nullable=False),
    Column("is_active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
)

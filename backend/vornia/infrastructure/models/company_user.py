"""Company-user relationship model."""

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from vornia.infrastructure.models.base import metadata

company_users = Table(
    "company_users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column("company_id", UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), nullable=False),
    Column("role", String(50), nullable=False, server_default="member"),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("company_id", "user_id", name="uq_company_user"),
)

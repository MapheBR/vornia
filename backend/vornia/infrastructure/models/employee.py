"""Employee model."""

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from vornia.infrastructure.models.base import metadata

employees = Table(
    "employees",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()),
    Column(
        "company_id",
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("control_id", BigInteger, nullable=True),
    Column("name", String, nullable=False),
    Column("registration", String, nullable=True),
    Column("pis", String, nullable=True),
    Column("cpf", String, nullable=True),
    Column("job_title", String, nullable=True),
    Column("department", String, nullable=True),
    Column("work_schedule", JSONB, nullable=True),
    Column("photo_url", String, nullable=True),
    Column("is_active", Boolean, nullable=False, server_default="true"),
    Column("hired_at", Date, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
)

"""Employee model."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Table,
    Text,
    func,
    text,
)
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
    Column("name", Text, nullable=False),
    Column("registration", Text, nullable=True),
    Column("pis", Text, nullable=True),
    Column("cpf", Text, nullable=True),
    Column("job_title", Text, nullable=True),
    Column("department", Text, nullable=True),
    Column("work_schedule", JSONB, nullable=True),
    Column("photo_url", Text, nullable=True),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("hired_at", Date, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
    Index("employees_company_active_idx", "company_id", "is_active"),
    Index(
        "employees_company_cpf_key",
        "company_id",
        "cpf",
        unique=True,
        postgresql_where=text("cpf IS NOT NULL"),
    ),
    Index(
        "employees_company_registration_key",
        "company_id",
        "registration",
        unique=True,
        postgresql_where=text("registration IS NOT NULL"),
    ),
    Index(
        "employees_company_control_id_key",
        "company_id",
        "control_id",
        unique=True,
        postgresql_where=text("control_id IS NOT NULL"),
    ),
)

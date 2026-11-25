"""Cria tabela processed_journeys com FORCE RLS (jornadas diárias processadas)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: str | Sequence[str] | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _claim() -> str:
    return (
        "(NULLIF(current_setting('request.jwt.claims', true), '')::json"
        " ->> 'company_id')::uuid"
    )


def upgrade() -> None:
    op.create_table(
        "processed_journeys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("entry", sa.Time(), nullable=True),
        sa.Column("lunch_exit", sa.Time(), nullable=True),
        sa.Column("lunch_return", sa.Time(), nullable=True),
        sa.Column("exit", sa.Time(), nullable=True),
        sa.Column("worked_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("expected_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("overtime_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("night_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_punch_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "company_id", "employee_id", "date", name="processed_journeys_tenant_day_key"
        ),
        sa.CheckConstraint(
            "status IN ('complete','pending','absence','inconsistency')",
            name="processed_journeys_status_check",
        ),
    )
    op.create_index(
        "processed_journeys_tenant_status_idx", "processed_journeys", ["company_id", "status"]
    )

    op.execute("ALTER TABLE processed_journeys ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE processed_journeys FORCE ROW LEVEL SECURITY;")
    claim = _claim()
    for action, clause in (
        ("select", f"USING (company_id = {claim})"),
        ("insert", f"WITH CHECK (company_id = {claim})"),
        ("update", f"USING (company_id = {claim}) WITH CHECK (company_id = {claim})"),
        ("delete", f"USING (company_id = {claim})"),
    ):
        op.execute(
            f"CREATE POLICY tenant_isolation_{action}_processed_journeys "
            f"ON processed_journeys FOR {action.upper()} {clause};"
        )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON processed_journeys TO vornia_app;")
    op.execute("GRANT DELETE ON processed_journeys TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("processed_journeys")

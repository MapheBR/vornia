"""Cria tabela raw_punches com FORCE RLS (batidas brutas do Control iD/CSV)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _claim() -> str:
    return (
        "(NULLIF(current_setting('request.jwt.claims', true), '')::json"
        " ->> 'company_id')::uuid"
    )


def upgrade() -> None:
    op.create_table(
        "raw_punches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("punched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_type", sa.Integer(), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
        ),
        sa.Column("processed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "mapping_status",
            sa.String(20),
            server_default=sa.text("'ok'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "source IN ('controlid','csv','manual')", name="raw_punches_source_check"
        ),
        sa.CheckConstraint(
            "mapping_status IN ('ok','unmapped')", name="raw_punches_mapping_check"
        ),
    )
    op.create_index(
        "raw_punches_tenant_punch_idx",
        "raw_punches",
        ["company_id", "employee_id", "punched_at"],
    )
    op.create_index(
        "raw_punches_tenant_processed_idx", "raw_punches", ["company_id", "processed"]
    )
    op.execute(
        """
        CREATE UNIQUE INDEX raw_punches_natural_key ON raw_punches
            (company_id, COALESCE(employee_id, '00000000-0000-0000-0000-000000000000'::uuid),
             punched_at, source, COALESCE(external_id, ''))
        """
    )

    op.execute("ALTER TABLE raw_punches ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE raw_punches FORCE ROW LEVEL SECURITY;")
    claim = _claim()
    for action, clause in (
        ("select", f"USING (company_id = {claim})"),
        ("insert", f"WITH CHECK (company_id = {claim})"),
        ("update", f"USING (company_id = {claim}) WITH CHECK (company_id = {claim})"),
        ("delete", f"USING (company_id = {claim})"),
    ):
        op.execute(
            f"CREATE POLICY tenant_isolation_{action}_raw_punches ON raw_punches "
            f"FOR {action.upper()} {clause};"
        )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON raw_punches TO vornia_app;")
    op.execute("GRANT DELETE ON raw_punches TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("raw_punches")

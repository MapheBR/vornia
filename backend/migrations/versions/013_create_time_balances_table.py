"""Cria tabela time_balances (saldo mensal por colaborador)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: str | Sequence[str] | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "time_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_month", sa.Date(), nullable=False),
        sa.Column("opening_balance", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("earned_hours", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("overtime_50_hours", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("overtime_100_hours", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("night_hours", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("owed_hours", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("closing_balance", sa.Numeric(8, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "employee_id", "reference_month", name="time_balances_tenant_month_key"),
    )
    op.execute("ALTER TABLE time_balances ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE time_balances FORCE ROW LEVEL SECURITY;")
    claim = "(\n        NULLIF(current_setting('request.jwt.claims', true), '')::json\n        ->> 'company_id'\n    )::uuid"
    for action, clause in (
        ("select", f"USING (company_id = {claim})"),
        ("insert", f"WITH CHECK (company_id = {claim})"),
        ("update", f"USING (company_id = {claim}) WITH CHECK (company_id = {claim})"),
        ("delete", f"USING (company_id = {claim})"),
    ):
        op.execute(
            f"CREATE POLICY tenant_isolation_{action}_time_balances ON time_balances "
            f"FOR {action.upper()} {clause};"
        )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON time_balances TO vornia_app;")
    op.execute("GRANT DELETE ON time_balances TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("time_balances")

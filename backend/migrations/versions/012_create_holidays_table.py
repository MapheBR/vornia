"""Cria tabela holidays por tenant (feriados com jornada especial)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: str | Sequence[str] | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "holidays",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("jornada_especial_hours", sa.Numeric(4, 2), server_default=sa.text("4.0"), nullable=False),
        sa.Column("recurring_yearly", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "date", name="holidays_tenant_date_key"),
    )
    op.execute("ALTER TABLE holidays ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE holidays FORCE ROW LEVEL SECURITY;")
    claim = "(\n        NULLIF(current_setting('request.jwt.claims', true), '')::json\n        ->> 'company_id'\n    )::uuid"
    for action, clause in (
        ("select", f"USING (company_id = {claim})"),
        ("insert", f"WITH CHECK (company_id = {claim})"),
        ("update", f"USING (company_id = {claim}) WITH CHECK (company_id = {claim})"),
        ("delete", f"USING (company_id = {claim})"),
    ):
        op.execute(
            f"CREATE POLICY tenant_isolation_{action}_holidays ON holidays "
            f"FOR {action.upper()} {clause};"
        )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON holidays TO vornia_app;")
    op.execute("GRANT DELETE ON holidays TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("holidays")

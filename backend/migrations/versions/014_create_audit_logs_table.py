"""Cria tabela audit_logs append-only (trilha de edição manual)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: str | Sequence[str] | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("before_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("audit_logs_tenant_entity_idx", "audit_logs", ["company_id", "entity_type", "entity_id"])
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;")
    claim = "(\n        NULLIF(current_setting('request.jwt.claims', true), '')::json\n        ->> 'company_id'\n    )::uuid"
    op.execute(
        f"CREATE POLICY tenant_isolation_select_audit_logs ON audit_logs FOR SELECT USING (company_id = {claim});"
    )
    op.execute(
        f"CREATE POLICY tenant_isolation_insert_audit_logs ON audit_logs FOR INSERT WITH CHECK (company_id = {claim});"
    )
    op.execute("GRANT SELECT, INSERT ON audit_logs TO vornia_app;")
    op.execute("GRANT SELECT, INSERT, DELETE ON audit_logs TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("audit_logs")

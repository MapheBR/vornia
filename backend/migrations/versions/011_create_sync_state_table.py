"""Cria tabela sync_state (cursor incremental por tenant e recurso)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: str | Sequence[str] | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _claim() -> str:
    return (
        "(NULLIF(current_setting('request.jwt.claims', true), '')::json"
        " ->> 'company_id')::uuid"
    )


def upgrade() -> None:
    op.create_table(
        "sync_state",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource", sa.String(30), nullable=False),
        sa.Column("last_cursor", sa.String(200), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default=sa.text("'idle'"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "resource", name="sync_state_tenant_resource_key"),
    )

    op.execute("ALTER TABLE sync_state ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE sync_state FORCE ROW LEVEL SECURITY;")
    claim = _claim()
    for action, clause in (
        ("select", f"USING (company_id = {claim})"),
        ("insert", f"WITH CHECK (company_id = {claim})"),
        ("update", f"USING (company_id = {claim}) WITH CHECK (company_id = {claim})"),
        ("delete", f"USING (company_id = {claim})"),
    ):
        op.execute(
            f"CREATE POLICY tenant_isolation_{action}_sync_state ON sync_state "
            f"FOR {action.upper()} {clause};"
        )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON sync_state TO vornia_app;")
    op.execute("GRANT DELETE ON sync_state TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("sync_state")

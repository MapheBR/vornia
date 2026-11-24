"""Cria tabela settings por empresa com FORCE RLS."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: str | Sequence[str] | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.UniqueConstraint("company_id", "key", name="settings_company_key_key"),
    )
    op.execute("ALTER TABLE settings ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE settings FORCE ROW LEVEL SECURITY;")

    claim = "(NULLIF(current_setting('request.jwt.claims', true), '')::json ->> 'company_id')::uuid"
    for action, clause in (
        ("select", f"USING (company_id = {claim})"),
        ("insert", f"WITH CHECK (company_id = {claim})"),
        ("update", f"USING (company_id = {claim}) WITH CHECK (company_id = {claim})"),
        ("delete", f"USING (company_id = {claim})"),
    ):
        op.execute(
            f"CREATE POLICY tenant_isolation_{action}_settings ON settings "
            f"FOR {action.upper()} {clause};"
        )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON settings TO vornia_app;")
    op.execute("GRANT DELETE ON settings TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("settings")

"""Cria tabela refresh_tokens com FORCE RLS e grants apenas para vornia_auth."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: str | Sequence[str] | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["replaced_by_id"], ["refresh_tokens.id"], ondelete="SET NULL"),
    )
    op.create_index("refresh_tokens_user_idx", "refresh_tokens", ["user_id"])
    op.create_index("refresh_tokens_family_idx", "refresh_tokens", ["family_id"])

    op.execute("ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE refresh_tokens FORCE ROW LEVEL SECURITY;")

    # Runtime (vornia_app) NAO tem grant nesta tabela: tokens so sao
    # manipulados pela role de bootstrap nos endpoints /auth/*.
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON refresh_tokens TO vornia_auth;")


def downgrade() -> None:
    op.drop_table("refresh_tokens")

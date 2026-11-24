"""Create employees table with tenant isolation via RLS."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "employees"
RUNTIME_ROLES = ("vornia_app", "vornia_auth")


def _company_id() -> str:
    """Extract company_id from the JSON claims set by set_rls_context()."""
    return (
        "(NULLIF(current_setting('request.jwt.claims', true), '')::json " "->> 'company_id')::uuid"
    )


def _create_policies(claim: str) -> None:
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_{TABLE} ON {TABLE}
            FOR SELECT USING (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_insert_{TABLE} ON {TABLE}
            FOR INSERT WITH CHECK (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_update_{TABLE} ON {TABLE}
            FOR UPDATE USING (company_id = {claim}) WITH CHECK (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_delete_{TABLE} ON {TABLE}
            FOR DELETE USING (company_id = {claim});
        """
    )


def _drop_policies() -> None:
    for operation in ("select", "insert", "update", "delete"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{operation}_{TABLE} ON {TABLE};")


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("control_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("registration", sa.Text(), nullable=True),
        sa.Column("pis", sa.Text(), nullable=True),
        sa.Column("cpf", sa.Text(), nullable=True),
        sa.Column("job_title", sa.Text(), nullable=True),
        sa.Column("department", sa.Text(), nullable=True),
        sa.Column("work_schedule", postgresql.JSONB(), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("hired_at", sa.Date(), nullable=True),
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
    )
    op.create_index("ix_employees_company_control_id", TABLE, ["company_id", "control_id"])
    op.create_index("ix_employees_company_pis", TABLE, ["company_id", "pis"])
    op.create_index("ix_employees_company_is_active", TABLE, ["company_id", "is_active"])

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY;")
    _create_policies(_company_id())

    roles = ", ".join(RUNTIME_ROLES)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {roles};")


def downgrade() -> None:
    roles = ", ".join(RUNTIME_ROLES)
    op.execute(f"REVOKE ALL ON {TABLE} FROM {roles};")
    _drop_policies()
    op.execute(f"ALTER TABLE {TABLE} NO FORCE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_employees_company_is_active", table_name=TABLE)
    op.drop_index("ix_employees_company_pis", table_name=TABLE)
    op.drop_index("ix_employees_company_control_id", table_name=TABLE)
    op.drop_table(TABLE)

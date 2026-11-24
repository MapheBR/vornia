"""Create employees table with tenant isolation."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _company_id() -> str:
    """Extract company_id from the JSON claims, treating empty GUC as no claim."""
    return (
        "(NULLIF(current_setting('request.jwt.claims', true), '')::json" " ->> 'company_id')::uuid"
    )


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("control_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("registration", sa.Text(), nullable=True),
        sa.Column("pis", sa.Text(), nullable=True),
        sa.Column("cpf", sa.Text(), nullable=True),
        sa.Column("job_title", sa.Text(), nullable=True),
        sa.Column("department", sa.Text(), nullable=True),
        sa.Column("work_schedule", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )

    op.create_index("employees_company_active_idx", "employees", ["company_id", "is_active"])
    op.create_index(
        "employees_company_cpf_key",
        "employees",
        ["company_id", "cpf"],
        unique=True,
        postgresql_where=sa.text("cpf IS NOT NULL"),
    )
    op.create_index(
        "employees_company_registration_key",
        "employees",
        ["company_id", "registration"],
        unique=True,
        postgresql_where=sa.text("registration IS NOT NULL"),
    )
    op.create_index(
        "employees_company_control_id_key",
        "employees",
        ["company_id", "control_id"],
        unique=True,
        postgresql_where=sa.text("control_id IS NOT NULL"),
    )

    op.execute("ALTER TABLE employees ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE employees FORCE ROW LEVEL SECURITY;")

    claim = _company_id()
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_employees ON employees
            FOR SELECT
            USING (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_insert_employees ON employees
            FOR INSERT
            WITH CHECK (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_update_employees ON employees
            FOR UPDATE
            USING (company_id = {claim})
            WITH CHECK (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_delete_employees ON employees
            FOR DELETE
            USING (company_id = {claim});
        """
    )

    op.execute("GRANT USAGE ON SCHEMA public TO vornia_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON employees TO vornia_app;")
    # Apenas DELETE: o uso de employees passa a ser via app;
    # vorestia_auth tambem e sujeito a RLS forçado, mas precisa de DELETE
    # para o cleanup da suíte de testes (tests/integration/conftest.py).
    op.execute("GRANT DELETE ON employees TO vornia;")


def downgrade() -> None:
    op.drop_table("employees")

"""Enable RLS and create tenant isolation policies."""

from collections.abc import Sequence

from alembic import op

revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tenant_company_id() -> str:
    return "current_setting('request.jwt.claims.company_id', true)::uuid"


def upgrade() -> None:
    op.execute("ALTER TABLE companies ENABLE ROW LEVEL SECURITY;")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_companies ON companies
            FOR SELECT
            USING (id = {_tenant_company_id()});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_insert_companies ON companies
            FOR INSERT
            WITH CHECK (id = {_tenant_company_id()});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_update_companies ON companies
            FOR UPDATE
            USING (id = {_tenant_company_id()});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_delete_companies ON companies
            FOR DELETE
            USING (id = {_tenant_company_id()});
        """
    )

    op.execute("ALTER TABLE company_users ENABLE ROW LEVEL SECURITY;")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_company_users ON company_users
            FOR SELECT
            USING (company_id = {_tenant_company_id()});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_insert_company_users ON company_users
            FOR INSERT
            WITH CHECK (company_id = {_tenant_company_id()});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_update_company_users ON company_users
            FOR UPDATE
            USING (company_id = {_tenant_company_id()});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_delete_company_users ON company_users
            FOR DELETE
            USING (company_id = {_tenant_company_id()});
        """
    )

    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_users ON users
            FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM company_users
                    WHERE company_users.user_id = users.id
                      AND company_users.company_id = {_tenant_company_id()}
                )
            );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_select_users ON users;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_delete_company_users ON company_users;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_update_company_users ON company_users;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_insert_company_users ON company_users;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_select_company_users ON company_users;")
    op.execute("ALTER TABLE company_users DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_delete_companies ON companies;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_update_companies ON companies;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_insert_companies ON companies;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_select_companies ON companies;")
    op.execute("ALTER TABLE companies DISABLE ROW LEVEL SECURITY;")

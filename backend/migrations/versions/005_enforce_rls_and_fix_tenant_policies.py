"""Enforce RLS, fix tenant claim extraction and grant runtime roles."""

from collections.abc import Sequence

from alembic import op

revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = ("companies", "company_users", "users")
RUNTIME_ROLES = ("vornia_app", "vornia_auth")


def _legacy_company_id() -> str:
    """Expression used by revision 004 (kept only for downgrade)."""
    return "current_setting('request.jwt.claims.company_id', true)::uuid"


def _company_id() -> str:
    """Extract company_id from the JSON claims set by set_rls_context().

    `current_setting('request.jwt.claims.company_id')` does not navigate JSON:
    it looks up a different, unset GUC and returns NULL. The whole value must be
    read and then parsed as JSON.

    NULLIF guards the pooled-connection case: after a transaction that used
    `set_config(..., true)`, the GUC is reset to an empty string, and `''::json`
    raises instead of yielding NULL. Both cases must mean "no claim" (0 rows).
    """
    return (
        "(NULLIF(current_setting('request.jwt.claims', true), '')::json" " ->> 'company_id')::uuid"
    )


def _drop_policies(table: str, suffixes: Sequence[str]) -> None:
    for suffix in suffixes:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{suffix}_{table} ON {table};")


def _companies_policies(claim: str) -> None:
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_companies ON companies
            FOR SELECT
            USING (id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_insert_companies ON companies
            FOR INSERT
            WITH CHECK (id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_update_companies ON companies
            FOR UPDATE
            USING (id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_delete_companies ON companies
            FOR DELETE
            USING (id = {claim});
        """
    )


def _company_users_policies(claim: str) -> None:
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_company_users ON company_users
            FOR SELECT
            USING (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_insert_company_users ON company_users
            FOR INSERT
            WITH CHECK (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_update_company_users ON company_users
            FOR UPDATE
            USING (company_id = {claim});
        """
    )
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_delete_company_users ON company_users
            FOR DELETE
            USING (company_id = {claim});
        """
    )


def _users_policies(claim: str) -> None:
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_select_users ON users
            FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM company_users
                    WHERE company_users.user_id = users.id
                      AND company_users.company_id = {claim}
                )
            );
        """
    )


def upgrade() -> None:
    # Superusers e roles com BYPASSRLS continuam fora do RLS de proposito:
    # vornia_auth usa isso apenas em register/login.
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    _drop_policies("companies", ("select", "insert", "update", "delete"))
    _drop_policies("company_users", ("select", "insert", "update", "delete"))
    _drop_policies("users", ("select",))

    claim = _company_id()
    _companies_policies(claim)
    _company_users_policies(claim)
    _users_policies(claim)

    roles = ", ".join(RUNTIME_ROLES)
    op.execute(f"GRANT USAGE ON SCHEMA public TO {roles};")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON companies, users, company_users TO {roles};"
    )


def downgrade() -> None:
    roles = ", ".join(RUNTIME_ROLES)
    op.execute(f"REVOKE ALL ON companies, users, company_users FROM {roles};")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {roles};")

    _drop_policies("companies", ("select", "insert", "update", "delete"))
    _drop_policies("company_users", ("select", "insert", "update", "delete"))
    _drop_policies("users", ("select",))

    claim = _legacy_company_id()
    _companies_policies(claim)
    _company_users_policies(claim)
    _users_policies(claim)

    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")

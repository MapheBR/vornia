-- Provisiona as roles de runtime do Vornia.
--
-- Modelo de privilegios:
--   * role owner (ex.: vornia)  -> roda migrations/Alembic e administra o schema
--   * vornia_app               -> runtime do FastAPI; sujeita a RLS (sem BYPASSRLS)
--   * vornia_auth              -> apenas register/login; BYPASSRLS para bootstrap de tenant
--
-- Executar como usuario administrador (superuser ou role com CREATEROLE):
--   psql -U postgres -d vornia \
--     -v app_password="$VORNIA_APP_PASSWORD" \
--     -v auth_password="$VORNIA_AUTH_PASSWORD" \
--     -f scripts/provision-db-roles.sql
--
-- Este script e idempotente.

\set ON_ERROR_STOP on

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vornia_app') THEN
        CREATE ROLE vornia_app LOGIN;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vornia_auth') THEN
        CREATE ROLE vornia_auth LOGIN BYPASSRLS;
    END IF;
END
$$;

-- Runtime: nunca pode ser owner, superuser ou bypassar RLS.
ALTER ROLE vornia_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;

-- Bootstrap: bypassa RLS de proposito, e usado somente em register/login.
ALTER ROLE vornia_auth LOGIN NOSUPERUSER BYPASSRLS NOCREATEDB NOCREATEROLE;


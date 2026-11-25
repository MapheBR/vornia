#!/bin/sh
# Provisiona as roles de runtime no primeiro start do container.
# Executado pelo entrypoint oficial do Postgres apenas quando o volume esta vazio.
set -eu

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    -f /docker-entrypoint-initdb.d/provision-db-roles.sql

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -c "ALTER ROLE vornia_app PASSWORD '${VORNIA_APP_PASSWORD:?VORNIA_APP_PASSWORD is required}'" \
    -c "ALTER ROLE vornia_auth PASSWORD '${VORNIA_AUTH_PASSWORD:?VORNIA_AUTH_PASSWORD is required}'"

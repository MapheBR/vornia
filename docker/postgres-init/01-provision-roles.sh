#!/bin/sh
# Provisiona as roles de runtime no primeiro start do container.
# Executado pelo entrypoint oficial do Postgres apenas quando o volume esta vazio.
set -eu

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    -v app_password="${VORNIA_APP_PASSWORD:?VORNIA_APP_PASSWORD is required}" \
    -v auth_password="${VORNIA_AUTH_PASSWORD:?VORNIA_AUTH_PASSWORD is required}" \
    -f /docker-entrypoint-initdb.d/provision-db-roles.sql

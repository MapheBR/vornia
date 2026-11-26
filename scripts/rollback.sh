#!/bin/sh
# Rollback para a versão anterior à tag atualmente deployada.
set -eu

APP_DIR="${1:-/opt/vornia}"
cd "$APP_DIR"

CURRENT="$(cat .deploy-version 2>/dev/null || true)"
if [ -z "$CURRENT" ]; then
    echo "Nenhuma versão deployada registrada em .deploy-version" >&2
    exit 1
fi

PREVIOUS="$(git describe --tags --abbrev=0 "$CURRENT^" 2>/dev/null || true)"
if [ -z "$PREVIOUS" ]; then
    echo "Não foi possível determinar a tag anterior a $CURRENT" >&2
    exit 1
fi

echo "Rollback: $CURRENT -> $PREVIOUS"
git fetch --tags --quiet
git checkout "$PREVIOUS"
echo "$PREVIOUS" > .deploy-version

export VORNIA_DOMAIN="$(cat .deploy-domain 2>/dev/null || echo localhost)"
export VORNIA_ACME_EMAIL="${VORNIA_ACME_EMAIL:-admin@localhost}"
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose exec -T backend alembic upgrade head

curl --fail --retry 10 --retry-delay 3 --retry-all-errors "https://$VORNIA_DOMAIN/health"
echo "Rollback concluído para $PREVIOUS"

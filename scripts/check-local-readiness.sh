#!/bin/sh
# Verifica a prontidão do computador local para o deploy do Vornia via Tailscale.
# Uso: ./scripts/check-local-readiness.sh [APP_DIR]
set -eu

APP_DIR="${1:-.}"
FAILED=0

check() {
    label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "OK    $label"
    else
        echo "FAIL  $label"
        FAILED=$((FAILED + 1))
    fi
}

echo "== Vornia local readiness =="
echo "App dir: $APP_DIR"

check "Docker instalado" docker --version
check "Docker Compose plugin" docker compose version
check "acesso ao Docker sem sudo" docker info
check "diretório da aplicação" test -d "$APP_DIR"
check ".env presente" test -f "$APP_DIR/.env"
check ".env com permissão restrita" sh -c 'test "$(stat -c %a "$1" 2>/dev/null || echo 600)" -le 600' sh "$APP_DIR/.env"
check "disco com >= 5 GB livres" sh -c 'test "$(df -Pm "$1" | tail -1 | awk "{print \$4}")" -ge 5000' sh "$APP_DIR"
check "Tailscale ativo com IP 100.x" sh -c 'tailscale ip -4 2>/dev/null | grep -q "^100\."'
check "compose local presente" test -f "$APP_DIR/docker-compose.local.yml"
check "Caddyfile local presente" test -f "$APP_DIR/docker/Caddyfile.prod"
check "porta 8080 livre ou Caddy" sh -c 'ss -ltn 2>/dev/null | grep -qE ":8080\b" || true'
check "health-check responde" sh -c 'curl -fsS http://localhost:8080/health 2>/dev/null | grep -q "ok"'

if [ "$FAILED" -ne 0 ]; then
    echo "Falhas: $FAILED. Não prosseguir com o deploy."
    exit 1
fi

echo "Computador local pronto para deploy."

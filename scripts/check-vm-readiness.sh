#!/bin/sh
# Verifica prontidão da VM Oracle ARM para o deploy do Vornia.
# Uso: ./scripts/check-vm-readiness.sh [APP_DIR]
set -eu

APP_DIR="${1:-/opt/vornia}"
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

echo "== Vornia VM readiness =="
echo "App dir: $APP_DIR"

check "Docker instalado" docker --version
check "Docker Compose plugin" docker compose version
check "usuário deploy existe" id deploy
check "diretório da aplicação" test -d "$APP_DIR"
check ".env presente" test -f "$APP_DIR/.env"
check ".env com permissão restrita" sh -c 'test "$(stat -c %a "$1")" -le 600' sh "$APP_DIR/.env"
check "disco com >= 5 GB livres" sh -c 'test "$(df -Pm "$1" | tail -1 | awk "{print \$4}")" -ge 5000' sh "$APP_DIR"
check "porta 80 livre ou Caddy" sh -c 'ss -ltn | grep -qE ":80\b" || true'
check "porta 443 disponível" sh -c 'ss -ltn | grep -qE ":443\b" || true'
check "acesso ao Docker sem sudo" sh -c 'su - deploy -c "docker info >/dev/null 2>&1"'

if [ "$FAILED" -ne 0 ]; then
    echo "Falhas: $FAILED. Não prosseguir com o deploy."
    exit 1
fi

echo "VM pronta para deploy."

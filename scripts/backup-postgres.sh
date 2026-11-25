#!/bin/sh
# Backup do PostgreSQL do Vornia com retenção de 7 dias.
# Uso:
#   BACKUP_DIR=/backups ./scripts/backup-postgres.sh
#   ./scripts/backup-postgres.sh --restore /backups/vornia_20260101_120000.sql.gz
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_URL="${DATABASE_URL:-postgresql://vornia:vornia@postgres:5432/vornia}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"

if [ "${1:-}" = "--restore" ]; then
    DUMP_FILE="${2:-}"
    if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
        echo "Uso: $0 --restore <arquivo.sql.gz>" >&2
        exit 2
    fi
    TMP_SQL="${DUMP_FILE%.gz}"
    gzip -cd "$DUMP_FILE" > "$TMP_SQL"
    # pg_dump 17 emite SET transaction_timeout; servidores 16 nao conhecem.
    sed -i '/^SET transaction_timeout/d' "$TMP_SQL"
    echo "Restaurando $TMP_SQL ..."
    psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$TMP_SQL"
    rm -f "$TMP_SQL"
    echo "Restore concluído."
    exit 0
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET="$BACKUP_DIR/vornia_$STAMP.sql.gz"
pg_dump "$DB_URL" | gzip > "$TARGET"
echo "Backup criado: $TARGET"

find "$BACKUP_DIR" -name 'vornia_*.sql.gz' -type f -mtime "+$RETENTION_DAYS" -delete

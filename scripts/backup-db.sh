#!/usr/bin/env bash
#
# Backup de la base de Piedras Rayadito.
#
# Pensado para el servidor local: vuelca Postgres comprimido, agrega la media
# (las fotos de producto viven en disco mientras no esten en object storage) y
# rota los backups viejos. Pensado para correr desde un systemd timer; ver
# docs/DEPLOY.md.
#
# Uso:  scripts/backup-db.sh [directorio-destino]
set -euo pipefail

BACKUP_DIR="${1:-${BACKUP_DIR:-/var/backups/rayadito}}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Credenciales desde el .env del proyecto, sin duplicarlas en otro lado.
# Se leen solo las claves necesarias en vez de hacer `source`: el .env tiene
# valores sin comillas con caracteres que bash interpretaria (por ejemplo
# DEFAULT_FROM_EMAIL, que lleva un nombre con `<` y `>`).
env_get() {
  [[ -f "$PROJECT_DIR/.env" ]] || return 0
  sed -n "s/^$1=//p" "$PROJECT_DIR/.env" | tail -1
}

DB_NAME="${DB_NAME:-$(env_get DB_NAME)}"
DB_USER="${DB_USER:-$(env_get DB_USER)}"
DB_PASSWORD="${DB_PASSWORD:-$(env_get DB_PASSWORD)}"
DB_HOST="${DB_HOST:-$(env_get DB_HOST)}"
DB_PORT="${DB_PORT:-$(env_get DB_PORT)}"

: "${DB_NAME:?falta DB_NAME}"
: "${DB_USER:?falta DB_USER}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"

STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

DUMP="$BACKUP_DIR/db-$STAMP.sql.gz"
echo "==> Volcando $DB_NAME a $DUMP"
PGPASSWORD="${DB_PASSWORD:-}" pg_dump \
  --host="$DB_HOST" --port="$DB_PORT" --username="$DB_USER" \
  --no-owner --no-privileges "$DB_NAME" | gzip > "$DUMP"

# Un dump vacio es peor que ninguno: avisa en vez de rotar sobre algo roto.
if [[ ! -s "$DUMP" ]]; then
  echo "ERROR: el dump quedo vacio" >&2
  exit 1
fi

MEDIA_DIR="$PROJECT_DIR/public"
if [[ -d "$MEDIA_DIR" ]]; then
  MEDIA="$BACKUP_DIR/media-$STAMP.tar.gz"
  echo "==> Empaquetando media en $MEDIA"
  tar -czf "$MEDIA" -C "$PROJECT_DIR" public
fi

echo "==> Borrando backups de mas de $RETENTION_DAYS dias"
find "$BACKUP_DIR" -maxdepth 1 -name '*.gz' -mtime "+$RETENTION_DAYS" -delete

echo "==> Listo. Contenido actual:"
ls -lh "$BACKUP_DIR" | tail -n +2

#!/usr/bin/env bash
#
# Trae los backups de produccion a este PC (copia fuera del disco del servidor).
#
# Corre en el PC de desarrollo, no en prod. Copia por rsync lo que deja
# rayadito-backup.timer en el servidor, verifica que cada gzip nuevo este
# integro y rota la copia local, que puede durar mas que la de prod.
#
# Uso:
#   scripts/pull-prod-backups.sh                  # una corrida
#   scripts/pull-prod-backups.sh --install-timer  # timer de usuario diario
#   scripts/pull-prod-backups.sh --remove-timer
#
# Variables opcionales:
#   PROD_HOST        alias SSH del servidor            (rayadito-prod)
#   REMOTE_DIR       carpeta de backups en el servidor (backups-rayadito, relativa al home)
#   DEST             carpeta local                     (~/respaldos/rayadito-prod)
#   KEEP_DB_DAYS     dias de dumps de base a conservar (90; pesan ~20 KB)
#   KEEP_MEDIA       tar de media a conservar          (3; pesan ~430 MB c/u)
set -euo pipefail

PROD_HOST="${PROD_HOST:-rayadito-prod}"
REMOTE_DIR="${REMOTE_DIR:-backups-rayadito}"
DEST="${DEST:-$HOME/respaldos/rayadito-prod}"
KEEP_DB_DAYS="${KEEP_DB_DAYS:-90}"
KEEP_MEDIA="${KEEP_MEDIA:-3}"
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
UNIT_DIR="$HOME/.config/systemd/user"

install_timer() {
  mkdir -p "$UNIT_DIR"
  cat > "$UNIT_DIR/rayadito-pull-backups.service" <<UNIT
[Unit]
Description=Traer backups de Piedras Rayadito desde produccion
After=network-online.target

[Service]
Type=oneshot
Environment=DEST=$DEST
ExecStart=$SCRIPT
UNIT
  # A las 05:00, despues del backup de prod (03:30). Persistent=true recupera
  # la corrida si el PC estaba apagado a esa hora.
  cat > "$UNIT_DIR/rayadito-pull-backups.timer" <<UNIT
[Unit]
Description=Traer backups de Piedras Rayadito una vez al dia

[Timer]
OnCalendar=*-*-* 05:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
UNIT
  systemctl --user daemon-reload
  systemctl --user enable --now rayadito-pull-backups.timer
  systemctl --user list-timers rayadito-pull-backups.timer --no-pager
}

case "${1:-}" in
  --install-timer) install_timer; exit 0 ;;
  --remove-timer)
    systemctl --user disable --now rayadito-pull-backups.timer || true
    rm -f "$UNIT_DIR"/rayadito-pull-backups.{service,timer}
    systemctl --user daemon-reload
    exit 0 ;;
  '') ;;
  *) echo "Uso: $0 [--install-timer|--remove-timer]" >&2; exit 2 ;;
esac

mkdir -p "$DEST"
before="$(mktemp)"
ls "$DEST" > "$before"

SSH=(ssh -o BatchMode=yes -o ConnectTimeout=15)
wanted="$(mktemp)"; trap 'rm -f "$before" "$wanted"' EXIT

# Se elige que traer en vez de dejarlo a rsync: sin eso, cada corrida volveria
# a bajar los tar de media que la rotacion local ya borro (430 MB cada uno).
remote="$("${SSH[@]}" "$PROD_HOST" "cd $REMOTE_DIR && ls -1")"
{
  grep -E '^db-.*\.sql\.gz$' <<<"$remote" || true
  grep -E '^media-.*\.tar\.gz$' <<<"$remote" | sort | tail -n "$KEEP_MEDIA" || true
} > "$wanted"

echo "==> rsync $PROD_HOST:$REMOTE_DIR/ -> $DEST/ ($(wc -l < "$wanted") archivos)"
# Sin --delete: la copia local no debe desaparecer porque prod rote.
rsync -a --partial -e "${SSH[*]}" --files-from="$wanted" \
  "$PROD_HOST:$REMOTE_DIR/" "$DEST/"

# Un archivo truncado es peor que ninguno: se borra para que la proxima
# corrida lo vuelva a traer, y el script termina con error.
broken=0
while read -r name; do
  [[ -n "$name" ]] || continue
  if gzip -t "$DEST/$name" 2>/dev/null; then
    echo "    ok  $name"
  else
    echo "ERROR: $name esta corrupto; se borra" >&2
    rm -f "$DEST/$name"
    broken=1
  fi
done < <(comm -13 "$before" <(ls "$DEST") | grep -E '\.gz$' || true)

echo "==> Rotando: dumps de mas de $KEEP_DB_DAYS dias, media salvo los $KEEP_MEDIA mas nuevos"
find "$DEST" -maxdepth 1 -name 'db-*.sql.gz' -mtime "+$KEEP_DB_DAYS" -delete
ls -1 "$DEST"/media-*.tar.gz 2>/dev/null | sort | head -n "-$KEEP_MEDIA" | xargs -r rm -f

newest="$(ls -1 "$DEST"/db-*.sql.gz 2>/dev/null | sort | tail -1)"
echo "==> Dump mas nuevo: ${newest:-ninguno}"
exit "$broken"

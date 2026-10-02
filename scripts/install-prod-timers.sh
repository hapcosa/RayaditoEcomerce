#!/usr/bin/env bash
#
# Timers de systemd de Piedras Rayadito en produccion.
#
# Genera las unidades con las rutas reales del checkout (no las de ejemplo de
# docs/DEPLOY.md) y, con --install, las instala y habilita. Sin argumentos solo
# las imprime: sirve para revisarlas antes de tocar /etc.
#
#   rayadito-backup           diario      scripts/backup-db.sh
#   rayadito-dispatch-notice  cada hora   manage.py notify_pending_dispatch
#   rayadito-instagram        cada 5 min  manage.py publish_instagram
#   rayadito-instagram-token  diario      manage.py instagram_token refresh
#                             (si el checkout ya trae el comando)
#   rayadito-billing          cada 10 min manage.py issue_tax_documents
#                             (solo si el .env tiene BILLING_MODE=provider)
#   rayadito-starken-tracking cada 2 h    manage.py starken_tracking
#                             (solo si el .env tiene STARKEN_ENABLED=true)
#
# Uso:
#   scripts/install-prod-timers.sh                 # imprime las unidades
#   sudo scripts/install-prod-timers.sh --install  # instala y habilita
#
# Variables opcionales: RUN_USER (dueño del checkout), BACKUP_DIR
# (~RUN_USER/backups-rayadito) y RETENTION_DAYS (14).
set -euo pipefail

MODE="${1:---print}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="${RUN_USER:-$(stat -c %U "$PROJECT_DIR")}"
RUN_HOME="$(getent passwd "$RUN_USER" | cut -d: -f6)"
BACKUP_DIR="${BACKUP_DIR:-$RUN_HOME/backups-rayadito}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
PYTHON="$PROJECT_DIR/.venv/bin/python"
UNIT_DIR=/etc/systemd/system

env_get() {
  [[ -f "$PROJECT_DIR/.env" ]] || return 0
  sed -n "s/^$1=//p" "$PROJECT_DIR/.env" | tail -1
}

# Sin EnvironmentFile= a proposito, igual que rayadito-api.service: settings.py
# lee el .env con django-environ, y el parser de systemd trata distinto los
# valores con caracteres especiales (SECRET_KEY tiene uno).
manage_service() {  # descripcion comando
  cat <<UNIT
[Unit]
Description=$1
After=network-online.target compose-rayadito.service
Wants=network-online.target

[Service]
Type=oneshot
User=$RUN_USER
Group=$RUN_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON manage.py $2
UNIT
}

timer() {  # descripcion calendario
  cat <<UNIT
[Unit]
Description=$1

[Timer]
OnCalendar=$2
# Si el PC estuvo apagado, la corrida perdida se ejecuta al arrancar.
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
UNIT
}

declare -A UNITS

UNITS[rayadito-backup.service]="$(cat <<UNIT
[Unit]
Description=Backup de Piedras Rayadito (base + media)
After=compose-rayadito.service

[Service]
Type=oneshot
User=$RUN_USER
Group=$RUN_USER
Environment=RETENTION_DAYS=$RETENTION_DAYS
ExecStart=$PROJECT_DIR/scripts/backup-db.sh $BACKUP_DIR
# Maquina compartida: que el tar de la media no le quite disco a nadie.
Nice=10
IOSchedulingClass=idle
UNIT
)"
UNITS[rayadito-backup.timer]="$(timer 'Backup diario de Piedras Rayadito' '*-*-* 03:30:00')"

UNITS[rayadito-dispatch-notice.service]="$(manage_service \
  'Aviso de plazo de despacho de Piedras Rayadito' notify_pending_dispatch)"
UNITS[rayadito-dispatch-notice.timer]="$(timer 'Revision horaria del plazo de despacho' hourly)"

UNITS[rayadito-instagram.service]="$(manage_service \
  'Publicaciones programadas de Instagram de Piedras Rayadito' publish_instagram)"
UNITS[rayadito-instagram.timer]="$(timer 'Revision de publicaciones de Instagram cada 5 minutos' '*:0/5')"

TIMERS=(rayadito-backup.timer rayadito-dispatch-notice.timer rayadito-instagram.timer)
SKIPPED=()

has_command() {
  [[ -f "$PROJECT_DIR/$1/management/commands/$2.py" ]]
}

# Los que dependen de un comando se instalan recien cuando el checkout lo
# trae: asi el orden en que se mergean los PR no deja un timer fallando.
if has_command social instagram_token; then
  UNITS[rayadito-instagram-token.service]="$(manage_service \
    'Renovacion del token de Instagram de Piedras Rayadito' 'instagram_token refresh')"
  UNITS[rayadito-instagram-token.timer]="$(timer 'Revision diaria del token de Instagram' '*-*-* 04:10:00')"
  TIMERS+=(rayadito-instagram-token.timer)
else
  SKIPPED+=("rayadito-instagram-token: este checkout no trae instagram_token")
fi

if [[ "$(env_get BILLING_MODE)" == provider ]]; then
  UNITS[rayadito-billing.service]="$(manage_service \
    'Emision y reintento de boletas/facturas de Piedras Rayadito' issue_tax_documents)"
  UNITS[rayadito-billing.timer]="$(timer 'Reintento de documentos tributarios cada 10 minutos' '*:0/10')"
  TIMERS+=(rayadito-billing.timer)
else
  SKIPPED+=("rayadito-billing: BILLING_MODE no es 'provider'")
fi

if [[ "$(env_get STARKEN_ENABLED)" == true ]] && has_command shipping starken_tracking; then
  UNITS[rayadito-starken-tracking.service]="$(manage_service \
    'Seguimiento de envios Starken de Piedras Rayadito' starken_tracking)"
  UNITS[rayadito-starken-tracking.timer]="$(timer 'Seguimiento de envios Starken cada 2 horas' '0/2:15')"
  TIMERS+=(rayadito-starken-tracking.timer)
else
  SKIPPED+=("rayadito-starken-tracking: STARKEN_ENABLED no es 'true' o falta el comando")
fi

case "$MODE" in
  --print)
    for name in $(printf '%s\n' "${!UNITS[@]}" | sort); do
      printf '### %s/%s\n%s\n\n' "$UNIT_DIR" "$name" "${UNITS[$name]}"
    done
    for reason in "${SKIPPED[@]}"; do
      echo "# omitido: $reason"
    done
    ;;
  --install)
    [[ $EUID -eq 0 ]] || { echo "ERROR: --install necesita sudo" >&2; exit 1; }
    [[ -x "$PYTHON" ]] || { echo "ERROR: no existe $PYTHON" >&2; exit 1; }
    install -d -o "$RUN_USER" -g "$RUN_USER" "$BACKUP_DIR"
    for name in "${!UNITS[@]}"; do
      printf '%s\n' "${UNITS[$name]}" > "$UNIT_DIR/$name"
      chmod 644 "$UNIT_DIR/$name"
      echo "==> $UNIT_DIR/$name"
    done
    systemctl daemon-reload
    systemctl enable --now "${TIMERS[@]}"
    systemctl list-timers 'rayadito-*' --no-pager
    ;;
  *)
    echo "Uso: $0 [--print|--install]" >&2
    exit 2
    ;;
esac

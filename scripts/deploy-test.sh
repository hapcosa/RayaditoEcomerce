#!/usr/bin/env bash
# Despliega la rama `test` en la maquina de pruebas (traderbot).
#
# Se ejecuta desde el checkout permanente en TEST_ROOT, no desde el workspace
# del runner: el .env, el venv y los media viven ahi y no deben recrearse en
# cada corrida.
#
# Uso: scripts/deploy-test.sh [<sha>]
set -euo pipefail

TEST_ROOT="${TEST_ROOT:-/mnt/datos/RayaditoEcomerce}"
LOG_DIR="${LOG_DIR:-/mnt/datos/rayadito-logs}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
REF="${1:-origin/test}"

export PATH="$HOME/.local/bin:$PATH"   # uv se instala fuera del PATH del sistema

cd "$TEST_ROOT"
mkdir -p "$LOG_DIR"

echo "==> Trayendo $REF"
git fetch origin test --quiet
git checkout --detach "$REF"
git log -1 --oneline

echo "==> Base de datos"
docker compose up -d db
# El healthcheck del compose tarda; esperar a que responda antes de migrar.
for _ in $(seq 1 30); do
  if docker compose exec -T db pg_isready -q; then break; fi
  sleep 2
done

echo "==> Dependencias del backend"
uv pip install --python "$TEST_ROOT/.venv/bin/python" -q -r requirements.txt

echo "==> Migraciones"
"$TEST_ROOT/.venv/bin/python" manage.py migrate --noinput
"$TEST_ROOT/.venv/bin/python" manage.py collectstatic --noinput >/dev/null

echo "==> Tests del backend"
"$TEST_ROOT/.venv/bin/python" manage.py test

echo "==> Frontend"
cd "$TEST_ROOT/web"
npm ci
npm run build
cd "$TEST_ROOT"

echo "==> Reiniciando servicios"
# pkill devuelve 1 si no habia nada que matar; en un arranque en frio es normal.
pkill -f "gunicorn core.wsgi" || true
pkill -f "next-server"        || true
sleep 2
nohup "$TEST_ROOT/.venv/bin/gunicorn" core.wsgi:application \
  -b "127.0.0.1:$BACKEND_PORT" -w "$GUNICORN_WORKERS" \
  >>"$LOG_DIR/django.log" 2>&1 &
( cd "$TEST_ROOT/web" && nohup npm run start >>"$LOG_DIR/next.log" 2>&1 & )

echo "==> Verificando"
ok=0
for _ in $(seq 1 30); do
  back=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$BACKEND_PORT/api/products/" || true)
  front=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FRONTEND_PORT/" || true)
  if [ "$back" = "200" ] && [ "$front" = "200" ]; then ok=1; break; fi
  sleep 2
done
if [ "$ok" != "1" ]; then
  echo "ERROR: backend=$back frontend=$front"
  tail -30 "$LOG_DIR/django.log" "$LOG_DIR/next.log"
  exit 1
fi
echo "OK: backend y frontend respondiendo 200"

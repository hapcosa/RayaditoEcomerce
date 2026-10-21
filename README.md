# Piedras Rayadito — Ecommerce

Ecommerce artesanal de **joyería y lapidación de piedras de Chiloé**.
Monorepo con tres partes:

| Carpeta | Qué es | Stack |
|---|---|---|
| raíz | API y admin de Django | Django + DRF + PostgreSQL |
| [`web/`](web/) | Tienda pública | Next.js 15 (App Router, TS, Tailwind) |
| [`admin-app/`](admin-app/) | App de administración | Expo / React Native |

- Guía para agentes/humanos y convenciones: **[`AGENTS.md`](AGENTS.md)**
- Plan de trabajo por fases: **[`docs/ROADMAP.md`](docs/ROADMAP.md)**
- Producción (Cloudflare Tunnel, systemd, backups): **[`docs/DEPLOY.md`](docs/DEPLOY.md)**
- Integraciones: [`STARKEN`](docs/STARKEN.md) · [`SII`](docs/SII.md) ·
  [`INSTAGRAM`](docs/INSTAGRAM.md) · [`WHATSAPP`](docs/WHATSAPP.md)

## Requisitos
- **Python 3.12** (igual que CI; las dependencias aún no soportan 3.13/3.14).
  Si tu sistema trae otra versión, [`uv`](https://docs.astral.sh/uv/) la instala
  sin tocar el Python del sistema.
- **Node 20+**
- **Docker** (para PostgreSQL local)

## Puesta en marcha (desarrollo)

```bash
# 1) Variables de entorno
cp .env.example .env                       # backend: ajusta si hace falta
cp web/.env.local.example web/.env.local   # tienda Next.js

# 2) Base de datos (PostgreSQL vía Docker)
docker compose up -d db       # expone Postgres en 127.0.0.1:15432

# 3) Backend (Django)
python3.12 -m venv .venv      # o: uv venv --python 3.12 .venv
source .venv/bin/activate
pip install -r requirements.txt   # o: uv pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo     # catálogo demo (opcional, idempotente)
python manage.py createsuperuser
python manage.py runserver     # http://127.0.0.1:8000

# 4) Tienda (Next.js) — en otra terminal
cd web
npm ci
npm run dev                    # http://localhost:3000
```

- Tienda: `http://localhost:3000`
- Admin de Django: `http://127.0.0.1:8000/admin/`
- Documentación de la API: `http://127.0.0.1:8000/api/docs`
- pgAdmin (opcional): `docker compose up -d pgadmin` → `http://127.0.0.1:8888`

La app admin (Expo) se configura aparte: ver [`admin-app/.env.example`](admin-app/.env.example).
Desde el teléfono no sirve `localhost`; usa la IP LAN de la máquina que corre Django.

## Comandos útiles
```bash
# Backend
python manage.py collectstatic --noinput   # una vez, antes de los tests (el admin lo necesita)
python manage.py test                      # tests backend

# Tienda (en web/)
npm run lint
npm run typecheck
npm run build
```

## Reglas de Git
Nada se sube directo a `master`. Cada cambio va en **su propia rama + worktree**, se abre
**PR** hacia `master`, **el merge lo hace el dueño del repo** y **CI debe pasar**.
Detalle en [`AGENTS.md`](AGENTS.md).

## Convenciones
- **Dinero:** entero **CLP** (sin decimales).
- **Secretos:** solo en `.env` (nunca en git).
- **Idioma:** UI/contenido en `es-CL`; código en inglés.

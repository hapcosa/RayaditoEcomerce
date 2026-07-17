# Piedras Rayadito — Ecommerce

Ecommerce artesanal de **joyería y lapidación de piedras de Chiloé**.
Monorepo: **Django + DRF + PostgreSQL** (backend) y **React + Vite** (frontend, en
migración a Next.js).

- Guía para agentes/humanos y convenciones: **[`AGENTS.md`](AGENTS.md)**
- Plan de trabajo por fases: **[`docs/ROADMAP.md`](docs/ROADMAP.md)**

## Requisitos
- **Python 3.12** (las dependencias no soportan 3.13/3.14 aún)
- **Node 20+**
- **Docker** (para PostgreSQL local)

## Puesta en marcha (desarrollo)

```bash
# 1) Variables de entorno
cp .env.example .env          # ajusta si hace falta

# 2) Base de datos (PostgreSQL vía Docker)
docker compose up -d db       # expone Postgres en el puerto 15432

# 3) Backend (Django)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo     # datos demo (opcional)
python manage.py createsuperuser
python manage.py runserver     # http://127.0.0.1:8000

# 4) Frontend (Vite) — en otra terminal
npm install
npm run dev                    # http://127.0.0.1:5173
```

- Admin de Django: `http://127.0.0.1:8000/admin/`
- pgAdmin (opcional): `docker compose up -d pgadmin` → `http://127.0.0.1:8888`

## Comandos útiles
```bash
python manage.py test          # tests backend
npm run build                  # build del front (Django sirve dist/)
npm run lint                   # lint del front
```

## Reglas de Git
Nada se sube directo a `master`. Cada cambio va en **su propia rama + worktree**, se abre
**PR** hacia `master`, **el merge lo hace el dueño del repo** y **CI debe pasar**.
Detalle en [`AGENTS.md`](AGENTS.md).

## Convenciones
- **Dinero:** entero **CLP** (sin decimales).
- **Secretos:** solo en `.env` (nunca en git).
- **Idioma:** UI/contenido en `es-CL`; código en inglés.

# AGENTS.md — Piedras Rayadito

Guía para agentes (Claude Code, Codex, Cursor, etc.) y humanos que trabajen en este repo.
Es la **fuente canónica**; `CLAUDE.md` la importa.

## Qué es este proyecto
Ecommerce artesanal de **joyería y lapidación de piedras de Chiloé** (marca *Piedras Rayadito*).
El repo base está pensado además como **template**: cada nuevo rubro (ej. textil) es un
**fork de git** que solo cambia branding + seed de atributos, sin tocar el modelo.

El plan completo y las fases están en **[`docs/ROADMAP.md`](docs/ROADMAP.md)** — léelo antes de
planificar trabajo grande.

## Stack
- **Backend:** Django + Django REST Framework + PostgreSQL. Auth con djoser + JWT (simplejwt) + OAuth Google/Facebook. Pagos MercadoPago. Envíos Starken (`django-starken`).
- **Frontend actual:** React 18 + Vite 4 + Redux (legacy). **En migración a Next.js** (App Router, TS) — ver ROADMAP Fase 4.
- **App admin:** (futura) Expo / React Native.
- **Redes:** (futura) Instagram Graph API + WhatsApp Cloud API — **solo APIs oficiales, nunca scraping**.
- Django sirve el build del front (`dist/`) hasta completar la migración a Next.js.

## Layout
```
core/            # settings, urls, wsgi/asgi del proyecto Django
user/ user_profile/   # cuenta (email login) y perfil/direcciones
category/        # categorías jerárquicas
metaproduct/     # atributos base (Material, NombrePiedra/Mohs)
product/         # Product → Joyas/Piedras, galería, reviews
carrito/         # carrito y items
orders/          # órdenes e items
payment/         # MercadoPago (make-payment, webhook, status)
shipping/        # opciones de envío (Starken)
src/             # frontend React/Vite (se migra a Next.js)
docs/ROADMAP.md  # plan de trabajo por fases
```

## Comandos
```bash
# Backend (usar Python 3.12 en venv; ver ROADMAP Fase 0)
python manage.py migrate
python manage.py runserver
python manage.py test            # tests

# Frontend (actual, Vite)
npm install
npm run dev
npm run build
npm run lint
```

## Convenciones
- **Dinero:** entero **CLP** (peso chileno, sin decimales) en toda la cadena. Nunca floats.
- **Secretos:** solo en `.env` (nunca en el código ni en git). Ver `.env.example`.
- **Idioma:** UI y contenido en `es-CL`. Código y nombres técnicos en inglés.
- **Estética:** artesanal/elegante (paleta tierra/piedra/ágata). Ver ROADMAP Fase 4.
- Mantén el código base **limpio y configurable** para que los forks sean livianos.

## Reglas de Git (obligatorias)
> **Nada se commitea ni se sube directo a `master`.**

1. **Un cambio = su propia rama en su propio worktree.**
   ```bash
   git worktree add ../rayadito-<tarea> -b <tipo>/<descripcion-corta>
   # tipos: feat, fix, chore, docs, refactor, test
   ```
2. Trabaja y commitea **en esa rama** (nunca en `master`).
3. Al terminar: `git push -u origin <rama>` y abre un **Pull Request** hacia `master`
   (`gh pr create --base master`).
4. **El merge a `master` lo hace el usuario**, nunca el agente.
5. **CI con tests debe pasar** antes del merge (ver `.github/workflows/ci.yml`).
6. Los agentes **no hacen `git push` a `master`** ni `merge`/`rebase` sobre `master`.
7. Commits en inglés, imperativo, con contexto (`feat: add product variants`).

## Definition of Done
- Rama + PR abiertos hacia `master` (no commits en master).
- CI verde (lint + build + tests).
- Sin secretos en el diff.
- Cambios de dinero/stock/pagos con tests.
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
- **Backend:** Django + Django REST Framework + PostgreSQL. Auth con djoser + JWT (simplejwt) + OAuth Google/Facebook. Pagos MercadoPago. Envíos Starken por su API oficial (apagado hasta tener credenciales; ver [`docs/STARKEN.md`](docs/STARKEN.md)). Boleta/factura SII (apagada; ver [`docs/SII.md`](docs/SII.md)).
- **Frontend:** Next.js 15 + React 19 (App Router, TS, Tailwind) en `web/`. El SPA de React/Vite se retiró en el cutover; su historia sigue en git.
- **App admin:** Expo / React Native en `admin-app/` (productos, fotos, órdenes, categorías/atributos, ventas, retractos). Habla con `/api/admin/` (solo staff).
- **Redes:** Instagram Graph API (publicar productos) + WhatsApp Cloud API (avisos de pedido), ambas apagadas hasta tener la cuenta Meta Business — **solo APIs oficiales, nunca scraping**. Ver [`docs/INSTAGRAM.md`](docs/INSTAGRAM.md) y [`docs/WHATSAPP.md`](docs/WHATSAPP.md).
- **Django ya no sirve la tienda.** Son dos procesos detrás del túnel de Cloudflare: Django en `/api/`, `/auth/`, `/admin/` y `/public/`, y Next.js en todo lo demás. Ver [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Layout
```
core/            # settings, urls, wsgi/asgi del proyecto Django
user/ user_profile/   # cuenta (email login) y perfil/direcciones
category/        # categorías jerárquicas
metaproduct/     # catálogos heredados (Material, NombrePiedra); lo nuevo va en product.Attribute
product/         # Product, atributos/variantes, stock, galería, reviews
carrito/         # carrito y items
orders/          # órdenes, items y derecho a retracto
payment/         # MercadoPago (make-payment, webhook, status)
shipping/        # opciones de envío, comunas y Starken
billing/         # boleta/factura SII
notifications/   # avisos por email, push (app admin) y WhatsApp
social/          # publicación en Instagram y su token
homepage/        # fotos de portada
wishlist/ suggestions/   # favoritos y buzón de sugerencias
web/             # tienda pública Next.js (App Router, TS)
admin-app/       # app admin Expo / React Native
scripts/         # deploy de test, backups y timers de producción
docs/            # ROADMAP, DEPLOY e integraciones (STARKEN, SII, INSTAGRAM, WHATSAPP)
```

## Comandos
```bash
# Backend (usar Python 3.12 en venv; ver ROADMAP Fase 0)
python manage.py migrate
python manage.py runserver
python manage.py collectstatic --noinput   # una vez, antes de los tests
python manage.py test            # tests

# Frontend (Next.js, en web/)
cd web
npm install
npm run dev        # http://localhost:3000
npm run build
npm run lint
npm run typecheck
```

## Convenciones
- **Marca y catálogos:** salen de [`store.json`](store.json) (nombre, dominio, textos, catálogos públicos). El backend lo lee en `settings.STORE` (ver `core/store.py`) y lo expone en `/api/store/`. Nunca escribas la marca ni los catálogos (`joya`/`piedra`) directo en el código: un fork solo cambia ese archivo. Los tests usan una tienda fija (`core/test_store.json`).
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
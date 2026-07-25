# Piedras Rayadito — Web (Next.js)

Tienda pública en **Next.js (App Router, TypeScript, Tailwind)**. Reemplaza
progresivamente al SPA de Vite (`../src`), que se mantiene como referencia hasta
completar la migración (ROADMAP **Fase 4**).

## Requisitos

- Node 18.18+ (probado con Node 20).
- La API DRF de Django corriendo (por defecto `http://127.0.0.1:8000/api`).

## Puesta en marcha

```bash
cd web
cp .env.local.example .env.local   # ajusta NEXT_PUBLIC_API_URL si hace falta
npm install
npm run dev                         # http://localhost:3000
```

Otros scripts:

```bash
npm run build       # build de producción
npm run start       # sirve el build
npm run lint        # eslint (next/core-web-vitals)
npm run typecheck   # tsc --noEmit
```

## Estructura

```
app/            # App Router (layout, páginas, globals.css con tokens)
lib/            # api.ts — acceso único a la API DRF
tailwind.config.ts  # design tokens (piedra / tierra / ágata) + tipografías
```

## Design system

Paleta artesanal de Chiloé expuesta como variables CSS en `app/globals.css`
(`--color-piedra-*`, `--color-tierra-*`, `--color-agata-*`) y mapeada a Tailwind
en `tailwind.config.ts`. Re-tematizar un fork (ROADMAP **Fase 8**) = sobrescribir
esas variables, sin tocar componentes. Tipografías: serif editorial (títulos),
sans (texto) y manuscrita (acentos).

## Pendiente (siguientes PRs de Fase 4)

Portar por páginas y unificar las 4 de detalle en 1: home real, catálogo
joyas/piedras, detalle, carrito, checkout, auth, dashboard, about, FAQ, contacto;
SEO (`sitemap.xml`, `robots`, datos estructurados), footer + buzón, estrellas y
wishlist. Ver `docs/ROADMAP.md`.

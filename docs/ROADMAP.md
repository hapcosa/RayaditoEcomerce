# Roadmap — Piedras Rayadito (ecommerce artesanal)

> Plan de trabajo para retomar y terminar el ecommerce de joyería y lapidación de piedras
> de Chiloé, y convertir el repo en **template** para forks de otros rubros artesanales.
>
> **Última actualización:** 2026-07-16

---

## 0. Decisiones arquitectónicas tomadas

| Tema | Decisión | Implicancia |
|------|----------|-------------|
| **Frontend** | Migrar a **Next.js** (App Router, TypeScript) | SEO real, imágenes optimizadas, base para diseño elegante. Se reescriben ~40 componentes React actuales. |
| **Template/forks** | **Fork de git por cliente** | El repo base se vuelve un *template repository*. Cada rubro (textil, etc.) es un fork que solo cambia branding + seed de atributos. El código base debe quedar limpio y configurable. |
| **App admin** | **Nativa con Expo / React Native** | Proyecto móvil aparte que consume la misma API DRF. Cámara nativa para subir productos. |
| **Redes sociales** | **APIs oficiales de Meta** | Instagram Graph API (publicar) + WhatsApp Business Cloud API (mensajes/catálogo). Sin scraping (riesgo de baneo). Requiere cuenta Meta Business verificada. |
| **Pagos** | MercadoPago (ya iniciado) | Robustecer webhook + máquina de estados. Moneda **CLP**. |
| **Envíos** | Starken (`django-starken` ya instalado) | Cotizador por comuna/región + generación de orden + tracking. |
| **Moneda** | CLP (peso chileno, **sin decimales**) | Normalizar todos los montos a enteros. |

---

## 1. Diagnóstico del estado actual

### Stack
Monorepo: **Django 5.0.6 + DRF + PostgreSQL** (backend) y **React 18 + Vite 4 + Redux** (frontend).
Django sirve el `dist/` de Vite. Deploy actual: Railway.

### Lo que ya funciona como base
- Auth completa: djoser + JWT + OAuth Google/Facebook, registro, activación por email, reset password.
- Modelos: `Product → Joyas/Piedras`, `Category` (jerárquica con `parent`), `Carrito`/`CarritoItem`, `Order`/`OrderItem`, `Payments`, `Shipping`, `UserProfile`.
- MercadoPago parcial: `payment/views.py` con `ProcessPaymentView`, webhook (`MercadoPagoResponse`), `StatusPaymentView`, Payment Bricks en el front.
- Empezado (front adelantado al back): reviews/estrellas, wishlist, coupons, FAQ, contacto, dashboard de perfil y direcciones.

### Bloqueadores para "retomar" (Fase 0, resolver primero)
1. **Python 3.14 instalado; Django no.** Deps viejas (`psycopg2==2.9.9`, `Django 5.0.6`) **no compilan en 3.14**. → Fijar **Python 3.12** + venv, subir a **Django 5.2 LTS** + **psycopg3**.
2. **No existe `.env`** y el settings lo exige (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS_DEPLOY`, credenciales DB).
3. **Secretos hardcodeados** (`sio28148` en `settings.py` y `docker-compose.yml`) → mover a env y **rotar**.
4. `CORS_ORIGIN_ALLOW_ALL=True` **con** `CORS_ALLOW_CREDENTIALS=True` → configuración insegura.
5. Reviews: el front llama `/api/reviews/...` pero **no existe la app/urls** en el backend (el modelo `reviews` vive suelto dentro de `product`).

### Deuda técnica a limpiar
**Frontend**
- `@material-ui/core@4` (MUI v4, sin mantención) — migrar o eliminar.
- `moment` (deprecado) → `date-fns` o `dayjs`.
- `redux` + `redux-thunk` sueltos → RTK ya los incluye; `redux-devtools-extension` (deprecado).
- `braintree-web-drop-in-react` — pasarela vieja, sobra (usamos MercadoPago).
- **3 stores** (`store.jsx`, `store2.jsx`, `store3.jsx`) → dejar uno.
- **4 páginas de detalle duplicadas** (`joyasDetail`, `joyasdetail1`, `joyasdetail2`, `JoyasTestDetail`) → unificar en 1.
- Redux escrito a mano (actions + reducers + `types.js`) en vez de slices RTK.

**Backend**
- `django-social-auth==0.7.28` (ancestral, choca con `social-auth-app-django`) — eliminar.
- `django-cors-middleware` (duplica `django-cors-headers`) — eliminar.
- `oauth2`, `python-openid`, `python3-openid`, `environ` (≠ `django-environ`), `pipfile`, `toml` — legacy/erróneas.
- `get-pip.py` (2.5 MB) commiteado, `vite.config.js.timestamp-*.mjs` vacío — basura en el repo.
- `docker-compose.yml` levanta MySQL **y** Postgres (contradictorio; el proyecto usa Postgres).

### Bugs de modelo detectados
- `CarritoItem` **no tiene cantidad** — no se puede comprar 2 del mismo ítem.
- `Product.price` (`decimal_places=0`) vs `compare_price` (`decimal_places=2`) — inconsistente; en CLP no van decimales.
- `sold = BooleanField` como único control de inventario — insuficiente (no hay stock).
- `reviews` sin FK a usuario, sin texto, sin 1–5, sin moderación.

---

## 2. Tabla de upgrades de dependencias

### Backend (requirements)
| Actual | Acción | Objetivo |
|--------|--------|----------|
| Django 5.0.6 | Subir | **Django 5.2 LTS** |
| psycopg2 2.9.9 | Reemplazar | **psycopg[binary] 3.x** |
| djangorestframework 3.15 | Subir | 3.16+ |
| djoser / simplejwt | Revisar compat 5.2 | últimas |
| mercadopago 2.2.1 | Subir | SDK actual |
| django-social-auth | **Eliminar** | (queda social-auth-app-django) |
| django-cors-middleware | **Eliminar** | (queda django-cors-headers) |
| oauth2, python-openid, python3-openid, environ, pipfile, toml | **Eliminar** | — |
| — | Agregar | **drf-spectacular** (OpenAPI), **sentry-sdk**, **django-storages** (ya está) + backend S3/R2 |

### Frontend (se rehace en Next.js)
La migración a Next.js reemplaza la mayoría. Equivalencias:
| Actual (Vite) | En Next.js |
|---------------|-----------|
| Redux legacy + thunk + persist | **RTK Query** o **React Query** + Server Components |
| @material-ui/core v4 | Tailwind + **shadcn/ui** o Radix |
| moment | date-fns |
| react-image-gallery / carousels varios | 1 sola librería moderna |
| @mercadopago/sdk-react 0.0.15 | SDK MercadoPago React actual |
| vite | next |

---

## 3. Modelo de datos objetivo (clave para los forks)

Aunque cada rubro sea un **fork de git**, el repo **base** debe traer un modelo de producto
genérico para que un fork (ej. textil) solo **configure y cargue seed**, sin tocar el schema.

```
Product (base, abstracto o con "type")
  ├─ name, slug, description (rich), price (CLP int), compare_price (CLP int)
  ├─ category (FK, jerárquica)
  ├─ status: draft/published, stock, is_featured
  └─ date_created

ProductImage (galería, orden, alt)

ProductVariant                 # una fila por combinación comprable
  ├─ product (FK)
  ├─ sku, price_override, stock
  └─ attributes (M2M → AttributeValue)

Attribute                      # "Talla", "Color", "Medida (cm)", "Material", "Dureza Mohs"
  └─ name, unit, kind (select/number/text)

AttributeValue                 # "M", "Rojo", "3.5", "Ágata"
  └─ attribute (FK), value

Review
  ├─ product (FK), user (FK), rating 1..5, comment
  ├─ verified_purchase (bool), approved (bool, moderación)
  └─ created_at

Suggestion  (buzón de sugerencias)
  └─ name, email, message, created_at, resolved
```

- **Joyas/Piedras** actuales pasan a ser **presets de atributos** (material, peso / largo-ancho-alto, tipo de piedra, Mohs), no subclases hardcodeadas.
- **Fork textil**: seed de atributos `Talla` (XS–XL), `Color`, `Medida (cm)`; sin cambiar modelos.
- Normalizar **dinero a entero CLP** en todo (price, compare_price, order amount, shipping).

---

## 4. Fases de ejecución

Cada fase lista **objetivo → tareas → entregable → criterio de aceptación (DoD)**.

### Fase 0 — Rescate y estabilización  ⏱️ base para todo
**Objetivo:** que el proyecto vuelva a correr localmente, seguro y reproducible.
- [ ] venv con **Python 3.12**; `requirements.txt` limpio (eliminar deps muertas de §2).
- [ ] Subir Django 5.2 LTS + psycopg3; correr `makemigrations`/`migrate`.
- [ ] Crear `.env.example` + `.env`; sacar **todos** los secretos de `settings.py` y `docker-compose.yml`; **rotar** contraseñas filtradas.
- [ ] `settings.py`: parsear `DEBUG` como bool, split dev/prod, CORS sin `ALLOW_ALL`+credentials, whitelist explícita.
- [ ] Limpiar repo: borrar `get-pip.py`, `vite.config.js.timestamp-*.mjs`, MySQL del compose.
- [ ] `docker-compose` solo Postgres + pgAdmin; script de seed (categorías, productos demo, envíos).
- [ ] Frontend actual: `npm install` + `build` funcionando como **referencia** antes de migrar.
- [ ] **Verificación E2E:** levantar back+front, cargar catálogo, login OK.

**DoD:** `python manage.py runserver` y `npm run dev` corren sin errores; catálogo y login funcionan; no hay secretos en git.

### Fase 1 — Saneamiento de backend / API genérica
**Objetivo:** API limpia, documentada y lista para Next.js + Expo.
- [ ] Refactor modelo a **variantes + atributos** (§3); migraciones de datos de Joyas/Piedras a presets.
- [ ] Arreglar `CarritoItem.quantity`; normalizar dinero CLP entero.
- [ ] Inventario/stock por variante (reemplazar `sold`).
- [ ] App **reviews** real (modelo + endpoints `/api/reviews/...` que el front ya espera) + rating agregado por producto + moderación.
- [ ] App/endpoint **buzón de sugerencias**.
- [ ] Slugs + endpoints REST consistentes; paginación; filtros/búsqueda.
- [ ] **drf-spectacular**: OpenAPI en `/api/schema` + Swagger UI.
- [ ] Tests de rutas críticas (carrito, orden, stock).

**DoD:** OpenAPI publicado; tests verdes; un fork textil podría cargar tallas/colores solo con seed.

### Fase 2 — Pagos (MercadoPago) robusto
**Objetivo:** cobrar de forma confiable en CLP.
- [ ] Subir `mercadopago` (py) y SDK React; elegir **Checkout Pro** o **Bricks** (hoy hay Bricks a medias).
- [ ] **Webhook seguro**: validar firma, idempotencia, máquina de estados de `Order` (no procesado→procesado→enviado / cancelado / rechazado).
- [ ] Manejar approved/pending/rejected/refunded; URLs success/failure/pending.
- [ ] Descontar stock al aprobar; evitar doble descuento (idempotencia).
- [ ] Cuotas; vista admin de pagos + conciliación.
- [ ] Pruebas en **sandbox** + checklist de go-live.

**DoD:** pago sandbox aprobado crea orden pagada + descuenta stock; webhook idempotente; estados correctos.

### Fase 3 — Envíos (Starken)
**Objetivo:** cotizar y despachar.
- [ ] Integrar `django-starken`: **cotizador** por comuna/región + peso/dimensiones.
- [ ] Regiones/comunas de Chile; sumar costo de envío al total del checkout.
- [ ] Generar orden de envío + guardar `deliveryNumber` (tracking).
- [ ] Opción de envío **manual** de respaldo; retiro en taller.
- [ ] (Dependencia externa: credenciales/API de Starken.)

**DoD:** el checkout muestra costo real por destino y guarda tracking al despachar.

### Fase 4 — Migración a Next.js + rediseño artesanal/elegante
**Objetivo:** tienda pública nueva, SEO y estética artesanal de Chiloé.
- [ ] Scaffold Next.js (App Router, TS, Tailwind, design system con tokens).
- [ ] **Lenguaje visual artesanal:** paleta de tierra/piedra/ágata, tipografía serif + acento manuscrito, texturas sutiles, mucho aire, fotografía grande. Referencias de joyería fina.
- [ ] Portar páginas y **unificar** las 4 de detalle en 1: home (portada nueva), catálogo joyas/piedras, detalle, carrito, checkout, auth, dashboard, about, FAQ, contacto.
- [ ] **SEO:** metadata, `sitemap.xml`, `robots`, datos estructurados `schema.org/Product`, OG images, `next/image`, i18n `es-CL`.
- [ ] **Footer completo:** contacto, mail del dominio, redes, links legales, buzón de sugerencias.
- [ ] Data fetching con RTK Query / React Query (fin del Redux legacy).
- [ ] UI de **estrellas**, **buzón**, **wishlist**.
- [ ] Accesibilidad (a11y) + performance (Core Web Vitals).

**DoD:** Lighthouse SEO/Perf/A11y altos; catálogo, detalle y checkout funcionando; footer y buzón activos.

### Fase 5 — App admin nativa (Expo)
**Objetivo:** subir productos y gestionar pedidos desde el celular.
- [ ] Proyecto Expo (TS) que consume la API DRF (endpoints staff + permisos por rol).
- [ ] Login staff; CRUD de productos con **cámara/galería** + compresión de imágenes.
- [ ] Gestión de pedidos y cambio de estado; ver ventas.
- [ ] Captura offline-friendly; manejo de tokens seguro.

**DoD:** desde el teléfono se crea un producto con fotos y se cambia el estado de un pedido.

### Fase 6 — Automatización social (APIs oficiales de Meta)
**Objetivo:** publicar y notificar sin arriesgar la cuenta.
- [ ] Setup Meta Business: cuenta IG Business ligada a página FB; verificación.
- [ ] **Instagram Graph API:** al crear producto, publicar foto + caption + hashtags (botón en la app Expo).
- [ ] **WhatsApp Cloud API:** confirmación de pedido, updates de envío, catálogo; con opt-in.
- [ ] Manejo de tokens de larga duración + colas/reintentos.

**DoD:** crear producto puede publicarlo en IG; un pedido dispara notificación WhatsApp.

### Fase 7 — Dominio, infra, deploy y hardening
**Objetivo:** producción seria.
- [ ] Comprar dominio → **email del dominio** (Zoho/Google Workspace) → SMTP real (hoy es `console.EmailBackend`).
- [ ] Media en **object storage** (S3 / Cloudflare R2 / Cloudinary — `cloudinary` ya está) vía django-storages.
- [ ] Deploy definitivo (Railway/Fly/Render) + Postgres administrado + backups.
- [ ] **Sentry**, rate limiting, security headers, HTTPS/HSTS.
- [ ] Legal Chile: términos, privacidad, Ley del Consumidor (botón de arrepentimiento), boleta/factura.

**DoD:** dominio con mail propio, media en storage, backups y monitoreo activos.

### Fase 8 — Template-ización para forks
**Objetivo:** que crear "el fork textil" tome horas, no semanas.
- [ ] Marcar el repo como **GitHub template repository**.
- [ ] Extraer TODO lo de marca/rubro a **config**: nombre, logo, paleta/tema, moneda, textos, redes (env + `branding.py` + theme tokens).
- [ ] **Seed fixtures por rubro**: joyería (material, Mohs) y textil (talla, color, medida cm).
- [ ] Doc "**Cómo crear un fork**": clonar template → cambiar branding → cargar atributos → seed → deploy.
- [ ] Script/checklist `create-fork`.

**DoD:** un fork textil nuevo queda operativo cambiando solo branding + seed, sin tocar modelos.

---

## 5. Temas transversales
- **Seguridad:** secretos solo en env; rotar lo filtrado; CORS/CSRF explícitos; validación de webhook; permisos por rol (cliente vs staff).
- **Dinero:** entero CLP en toda la cadena; nunca floats.
- **Testing:** pytest-django en rutas de dinero/stock/orden; e2e básico del checkout.
- **i18n:** base `es-CL`; dejar preparado para traducir (útil para forks).
- **Observabilidad:** Sentry + logs estructurados.
- **CI/CD:** lint + tests + build en cada push; deploy por rama.

## 6. Orden recomendado y dependencias
```
Fase 0 (rescate)  ─┬─► Fase 1 (API genérica) ─┬─► Fase 2 (pagos) ─► Fase 3 (envíos)
                   │                           │
                   │                           └─► Fase 4 (Next.js) ──► Fase 5 (Expo) ─► Fase 6 (Meta)
                   │
                   └─► Fase 7 (infra) en paralelo   Fase 8 (template) al final / continuo
```
- **Fase 0 es prerequisito de todo.**
- Fase 4 (Next.js) puede arrancar apenas la API de Fase 1 esté estable.
- Fases 5 y 6 dependen de API estable (Fase 1) y de cuentas Meta Business.

## 7. Dependencias externas / a gestionar por el dueño
- Compra de **dominio** + email.
- **MercadoPago:** credenciales prod + activación de cuenta.
- **Starken:** acceso/credenciales de su API.
- **Meta Business:** verificación, IG Business + página FB, número WhatsApp Business.
- **Hosting** de producción + storage de media.

## 8. Riesgos
- Migración a Next.js reescribe el front (mayor esfuerzo inicial; mitiga: portar por páginas, mantener el SPA como referencia hasta cortar).
- Meta puede requerir revisión de app para IG/WhatsApp (tiempos externos).
- "Fork por git" tiende a divergir: mitiga manteniendo el **template limpio y configurable** y portando fixes con cherry-pick.
```
# Deploy — servidor local + túnel de Cloudflare

Piedras Rayadito corre en un **PC propio**, expuesto a internet por un **túnel de
Cloudflare** con dominio propio. No hay PaaS ni balanceador: el túnel es el único
punto de entrada, y Cloudflare termina el TLS.

Desde el cutover a Next.js, **Django ya no sirve la tienda**. Son dos procesos:

| Proceso | Puerto local | Qué sirve |
|---|---|---|
| Django (gunicorn) | `8000` | `/api/`, `/auth/`, `/admin/`, `/ckeditor5/`, `/assets/` (estáticos del admin) y `/public/` (media) |
| Next.js (`next start`) | `3000` | Todo el resto: la tienda pública |

El ruteo por path lo hace `cloudflared`, así que no hace falta nginx.

## 1. Túnel

```bash
cloudflared tunnel login
cloudflared tunnel create rayadito
cloudflared tunnel route dns rayadito piedrasrayadito.cl
```

`~/.cloudflared/config.yml` — **el orden importa**: la primera regla que
coincide gana, así que las rutas del backend van antes del catch-all de Next.

```yaml
tunnel: rayadito
credentials-file: /home/USUARIO/.cloudflared/UUID.json

ingress:
  # Backend Django.
  - hostname: piedrasrayadito.cl
    path: ^/(api|auth|admin|ckeditor5|assets|public)(/.*)?$
    service: http://localhost:8000
  # Tienda pública Next.js.
  - hostname: piedrasrayadito.cl
    service: http://localhost:3000
  - service: http_status:404
```

Probar la config antes de instalarla como servicio:

```bash
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://piedrasrayadito.cl/api/products/
```

## 2. Variables de entorno (`.env`)

```bash
DEBUG=false
ALLOWED_HOSTS=piedrasrayadito.cl,www.piedrasrayadito.cl,127.0.0.1

# Django está detrás del túnel: confiar en el Host y el proto reenviados para
# que las URLs absolutas (webhook de MercadoPago incluido) usen el dominio real.
USE_X_FORWARDED_HOST=true

# Cloudflare ya fuerza HTTPS; el redirect acá solo agrega un salto.
SECURE_SSL_REDIRECT=false
SECURE_HSTS_SECONDS=31536000

CORS_ALLOWED_ORIGINS=https://piedrasrayadito.cl
CSRF_TRUSTED_ORIGINS=https://piedrasrayadito.cl

FRONTEND_BASE_URL=https://piedrasrayadito.cl
MERCADOPAGO_NOTIFICATION_URL=https://piedrasrayadito.cl/api/payment/webhook
```

Y en `web/.env.local`:

```bash
NEXT_PUBLIC_BACKEND_URL=https://piedrasrayadito.cl
NEXT_PUBLIC_API_URL=https://piedrasrayadito.cl/api
NEXT_PUBLIC_SITE_URL=https://piedrasrayadito.cl
```

> Con el mismo dominio para ambos, `mediaUrl()` deja de cruzar orígenes y las
> imágenes se sirven desde `/public/...` del propio sitio.

## 3. Servicios systemd

`/etc/systemd/system/rayadito-api.service`:

```ini
[Unit]
Description=Piedras Rayadito - API Django
After=network.target postgresql.service

[Service]
User=USUARIO
WorkingDirectory=/home/USUARIO/rayadito
EnvironmentFile=/home/USUARIO/rayadito/.env
ExecStart=/home/USUARIO/rayadito/.venv/bin/gunicorn core.wsgi:application \
    --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/rayadito-web.service`:

```ini
[Unit]
Description=Piedras Rayadito - Tienda Next.js
After=network.target

[Service]
User=USUARIO
WorkingDirectory=/home/USUARIO/rayadito/web
ExecStart=/usr/bin/npm run start
Environment=NODE_ENV=production PORT=3000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now rayadito-api rayadito-web
sudo cloudflared service install
```

## 4. Despliegue de una versión

```bash
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput   # estáticos del admin
(cd web && npm ci && npm run build)
sudo systemctl restart rayadito-api rayadito-web
```

## 5. Verificación post-deploy

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://piedrasrayadito.cl/            # 200, Next
curl -s -o /dev/null -w '%{http_code}\n' https://piedrasrayadito.cl/api/products/  # 200, Django
curl -s https://piedrasrayadito.cl/api/ruta-inexistente                          # 404 JSON del backend
curl -s -o /dev/null -w '%{http_code}\n' https://piedrasrayadito.cl/admin/login/  # 200
```

Que `/api/ruta-inexistente` devuelva **JSON** y no HTML confirma que el catch-all
del SPA ya no está y que el proxy separa bien los dos procesos.

## Por qué no hay `build.sh` ni `procfile`

Los dos venían del intento de deploy en Railway y quedaron obsoletos con este
setup: llamaban a `npm run build` del SPA de Vite (que ya no existe), y además
arrastraban bugs viejos — `collectstatic --no-imput`, `runserver` como comando
de arranque y `gunicorn core.wsgi` sin `:application`. El despliegue ahora es el
de este documento: systemd + `cloudflared`.

## Pendientes de esta fase

- **Media en object storage** (S3 / R2 / Cloudinary) vía `django-storages`. Hoy
  las fotos viven en el disco del PC: si se pierde, se pierden.
- **Backups** de Postgres.
- **SMTP real**: el backend de correo sigue siendo `console.EmailBackend`.
- **Sentry** y rate limiting.

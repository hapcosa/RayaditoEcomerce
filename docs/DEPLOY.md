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
cloudflared tunnel route dns rayadito piedrasdelrayadito.cl
```

`~/.cloudflared/config.yml` — **el orden importa**: la primera regla que
coincide gana, así que las rutas del backend van antes del catch-all de Next.

```yaml
tunnel: rayadito
credentials-file: /home/USUARIO/.cloudflared/UUID.json

ingress:
  # Backend Django.
  - hostname: piedrasdelrayadito.cl
    path: ^/(api|auth|admin|ckeditor5|assets|public)(/.*)?$
    service: http://localhost:8000
  # Tienda pública Next.js.
  - hostname: piedrasdelrayadito.cl
    service: http://localhost:3000
  - service: http_status:404
```

Probar la config antes de instalarla como servicio:

```bash
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://piedrasdelrayadito.cl/api/products/
```

## 2. Variables de entorno (`.env`)

```bash
DEBUG=false
ALLOWED_HOSTS=piedrasdelrayadito.cl,www.piedrasdelrayadito.cl,127.0.0.1

# Django está detrás del túnel: confiar en el Host y el proto reenviados para
# que las URLs absolutas (webhook de MercadoPago incluido) usen el dominio real.
USE_X_FORWARDED_HOST=true

# Cloudflare ya fuerza HTTPS; el redirect acá solo agrega un salto.
SECURE_SSL_REDIRECT=false
SECURE_HSTS_SECONDS=31536000

CORS_ALLOWED_ORIGINS=https://piedrasdelrayadito.cl
CSRF_TRUSTED_ORIGINS=https://piedrasdelrayadito.cl

# Login social: el callback de prod debe estar aqui Y registrado como
# "URI de redireccionamiento autorizado" en la consola del proveedor.
SOCIAL_AUTH_ALLOWED_REDIRECT_URIS=https://piedrasdelrayadito.cl/auth/social/callback

FRONTEND_BASE_URL=https://piedrasdelrayadito.cl
MERCADOPAGO_NOTIFICATION_URL=https://piedrasdelrayadito.cl/api/payment/webhook
```

Y en `web/.env.local`:

```bash
NEXT_PUBLIC_BACKEND_URL=https://piedrasdelrayadito.cl
NEXT_PUBLIC_API_URL=https://piedrasdelrayadito.cl/api
NEXT_PUBLIC_SITE_URL=https://piedrasdelrayadito.cl

NEXT_PUBLIC_CONTACT_EMAIL=contacto@piedrasdelrayadito.cl
NEXT_PUBLIC_INSTAGRAM_URL=https://instagram.com/piedrasdelrayadito
NEXT_PUBLIC_WHATSAPP_URL=https://wa.me/56950416291
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
curl -s -o /dev/null -w '%{http_code}\n' https://piedrasdelrayadito.cl/            # 200, Next
curl -s -o /dev/null -w '%{http_code}\n' https://piedrasdelrayadito.cl/api/products/  # 200, Django
curl -s https://piedrasdelrayadito.cl/api/ruta-inexistente                          # 404 JSON del backend
curl -s -o /dev/null -w '%{http_code}\n' https://piedrasdelrayadito.cl/admin/login/  # 200
```

Que `/api/ruta-inexistente` devuelva **JSON** y no HTML confirma que el catch-all
del SPA ya no está y que el proxy separa bien los dos procesos.

## Por qué no hay `build.sh` ni `procfile`

Los dos venían del intento de deploy en Railway y quedaron obsoletos con este
setup: llamaban a `npm run build` del SPA de Vite (que ya no existe), y además
arrastraban bugs viejos — `collectstatic --no-imput`, `runserver` como comando
de arranque y `gunicorn core.wsgi` sin `:application`. El despliegue ahora es el
de este documento: systemd + `cloudflared`.

## 6. Chequeos de configuración

El proyecto trae chequeos propios que corren con `manage.py check --deploy` y
fallan si falta algo que **no rompe el arranque pero sí el negocio**:

| ID | Qué detecta |
|---|---|
| `rayadito.E001` | `EMAIL_BACKEND` imprime en consola: activación de cuenta y reseteo de contraseña no llegan a nadie |
| `rayadito.E002` | Falta `MERCADOPAGO_ACCESS_TOKEN`: el checkout devuelve 500 |
| `rayadito.W001` | La media está en el disco del servidor y no en object storage |

Corrélos como paso previo al deploy:

```bash
.venv/bin/python manage.py check --deploy --fail-level ERROR
```

Son inertes con `DEBUG=True`, así que no molestan en desarrollo.

## 7. Media en object storage

Mientras `MEDIA_STORAGE=local` (el default), las fotos viven en `public/` del
servidor y las sirve Django. Para moverlas a S3 o Cloudflare R2, sin tocar
código:

```bash
MEDIA_STORAGE=s3
AWS_STORAGE_BUCKET_NAME=rayadito-media
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_ENDPOINT_URL=https://<cuenta>.r2.cloudflarestorage.com   # solo R2
```

Las fotos ya subidas hay que copiarlas al bucket a mano (`rclone`/`aws s3 sync`
sobre `public/photos/`); las rutas guardadas en la base son relativas y siguen
resolviendo.

## 8. Backups

`scripts/backup-db.sh` vuelca Postgres comprimido, empaqueta la media y rota lo
viejo (14 días por defecto, `RETENTION_DAYS` lo cambia).

```bash
scripts/backup-db.sh /var/backups/rayadito
```

Automatizado con un timer de systemd:

`/etc/systemd/system/rayadito-backup.service`:

```ini
[Unit]
Description=Backup de Piedras Rayadito

[Service]
Type=oneshot
User=USUARIO
ExecStart=/home/USUARIO/rayadito/scripts/backup-db.sh /var/backups/rayadito
```

`/etc/systemd/system/rayadito-backup.timer`:

```ini
[Unit]
Description=Backup diario de Piedras Rayadito

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now rayadito-backup.timer
```

> Un backup que nunca se restauró no es un backup. Probá la restauración al
> menos una vez:
> `zcat db-XXXX.sql.gz | psql -h 127.0.0.1 -U USUARIO -d rayadito_restore_test`

**El backup vive en el mismo disco que la base.** Copiá `/var/backups/rayadito`
a otro lado (otro disco, R2, un NAS) o un solo fallo se lleva las dos cosas.

## 9. Rate limiting

Sin nada delante que limite, el freno vive en DRF. Es **solo por scope**, a
propósito: un límite global por IP contaría juntas todas las peticiones que
Next hace al renderizar en el servidor y tumbaría el sitio con poco tráfico.

| Scope | Default | Vista |
|---|---|---|
| `payment` | 10/min | `ProcessPaymentView` — crea orden y pega a MercadoPago |
| `suggestions` | 5/min | buzón público sin auth |
| `reviews` | 20/min | crear reseña |

Ajustables por env (`THROTTLE_PAYMENT`, etc.). El webhook de MercadoPago está
exento: reintenta ante fallos y frenarlo perdería confirmaciones de pago.

**`NUM_PROXIES` hay que verificarlo contra el sitio desplegado.** Detrás del
túnel la IP real llega en `X-Forwarded-For`; si el valor no coincide con la
cantidad de proxies que la agregan, o todos los visitantes comparten cuota, o
un atacante puede falsear su IP. Comprobalo con:

```bash
curl -s https://piedrasdelrayadito.cl/api/products/ -H 'X-Forwarded-For: 1.2.3.4'
```

y revisando a quién le imputó la petición el throttle.

> Con varios workers de gunicorn cada uno tiene su propia caché en memoria, así
> que el límite efectivo se multiplica por la cantidad de workers. Sirve como
> freno grueso; si hace falta precisión, apuntá `CACHE_URL` a un Redis.

## 10. Sentry

Opt-in: sin `SENTRY_DSN` no se inicializa nada.

```bash
SENTRY_DSN=https://...ingest.sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

`send_default_pii` está en `False`: no se mandan emails ni direcciones de
clientes a un tercero.

## Pendientes de esta fase

- **Correo real:** hoy `EMAIL_BACKEND` es `console.EmailBackend` y los mails no
  se envían. Requiere dominio + casilla (Zoho/Google Workspace).
- **Legal Chile:** botón de arrepentimiento, boleta/factura, y revisar el
  contenido de `/terminos` y `/privacidad`.
- **Rotar la contraseña de la base de datos**: la que se usó hasta la Fase 0
  quedó en el historial de git de este repo, que es publico. Ver `docs/ROADMAP.md`.

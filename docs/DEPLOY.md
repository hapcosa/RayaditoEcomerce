# Deploy — servidor local + túnel de Cloudflare

Piedras Rayadito corre en un **PC propio**, expuesto a internet por un **túnel de
Cloudflare** con dominio propio. No hay PaaS ni balanceador: el túnel es el único
punto de entrada, y Cloudflare termina el TLS.

Desde el cutover a Next.js, **Django ya no sirve la tienda**. Son dos procesos:

| Proceso | Puerto local | Qué sirve |
|---|---|---|
| Django (gunicorn) | `8010` | `/api/`, `/auth/`, `/admin/`, `/ckeditor5/`, `/assets/` (estáticos del admin) y `/public/` (media) |
| Next.js (`next start`) | `3010` | Todo el resto: la tienda pública |

El ruteo por path lo hace `cloudflared`, así que no hace falta nginx.

> **Los puertos no son sagrados: verificalos.** El servidor es una máquina
> compartida con otros proyectos, y `8000` y `3000` —los defaults obvios— ya
> están tomados ahí. Antes de escribir el `config.yml`, corré `ss -ltn` y
> confirmá que los puertos que vas a usar estén libres. Apuntar el túnel a un
> puerto ajeno **publica el servicio de otro proyecto en
> `piedrasdelrayadito.cl`**, sin ningún error visible: el túnel levanta
> perfecto y el dominio devuelve 200.

## 1. Túnel

### Máquina compartida: instancia propia

En el servidor ya corre `cloudflared` **autenticado contra otra cuenta de
Cloudflare**, sirviendo túneles de terceros. `cloudflared` maneja una sola
cuenta por `cert.pem`, así que Rayadito necesita su propio directorio y su
propia instancia. **No toques `~/.cloudflared/` ni `/etc/cloudflared/`**:
sobrescribir ese `cert.pem` deja los túneles ajenos sin administración.

`cloudflared tunnel login` escribe siempre en `~/.cloudflared/cert.pem` e
**ignora** tanto `--origincert` como `$TUNNEL_ORIGIN_CERT`. Hay que apartar el
existente y devolverlo después:

```bash
mv ~/.cloudflared/cert.pem ~/.cloudflared/cert.pem.otracuenta
cloudflared tunnel login          # entrar con la cuenta de Rayadito
mkdir -p ~/.cloudflared-rayadito
mv ~/.cloudflared/cert.pem ~/.cloudflared-rayadito/cert.pem
mv ~/.cloudflared/cert.pem.otracuenta ~/.cloudflared/cert.pem
```

Los túneles en marcha no se caen durante la maniobra: se autentican con sus
JSON de credenciales, no con `cert.pem`.

### Crear el túnel

```bash
export TUNNEL_ORIGIN_CERT=$HOME/.cloudflared-rayadito/cert.pem
cloudflared tunnel create \
  --credentials-file $HOME/.cloudflared-rayadito/rayadito.json rayadito
cloudflared tunnel route dns rayadito piedrasdelrayadito.cl
cloudflared tunnel route dns rayadito www.piedrasdelrayadito.cl
```

`~/.cloudflared-rayadito/config.yml` — **el orden importa**: la primera regla
que coincide gana, así que las rutas del backend van antes del catch-all de
Next.

```yaml
tunnel: UUID
credentials-file: /home/USUARIO/.cloudflared-rayadito/rayadito.json
origincert: /home/USUARIO/.cloudflared-rayadito/cert.pem

ingress:
  # --- Backend Django ---
  - hostname: piedrasdelrayadito.cl
    path: ^/(api|admin|ckeditor5|assets|public)(/.*)?$
    service: http://localhost:8010
  - hostname: www.piedrasdelrayadito.cl
    path: ^/(api|admin|ckeditor5|assets|public)(/.*)?$
    service: http://localhost:8010
  # djoser: solo estos tres prefijos bajo /auth son del backend.
  - hostname: piedrasdelrayadito.cl
    path: ^/auth/(users|jwt|o)(/.*)?$
    service: http://localhost:8010
  - hostname: www.piedrasdelrayadito.cl
    path: ^/auth/(users|jwt|o)(/.*)?$
    service: http://localhost:8010
  # social_django cuelga de la raíz (core/urls.py: path('', ...)).
  - hostname: piedrasdelrayadito.cl
    path: ^/(login|complete|disconnect)/.*$
    service: http://localhost:8010
  - hostname: www.piedrasdelrayadito.cl
    path: ^/(login|complete|disconnect)/.*$
    service: http://localhost:8010

  # --- Tienda pública Next.js ---
  - hostname: piedrasdelrayadito.cl
    service: http://localhost:3010
  - hostname: www.piedrasdelrayadito.cl
    service: http://localhost:3010
  - service: http_status:404
```

> **`/auth` está compartido entre los dos procesos.** Django tiene ahí los
> endpoints de djoser (`/auth/users`, `/auth/jwt`, `/auth/o`) y Next tiene las
> páginas `/auth/login`, `/auth/registro`, `/auth/reset` y
> `/auth/social/callback`. Mandar `/auth` entero al backend deja la tienda sin
> login: la página devuelve el 404 JSON de Django. Por eso las reglas nombran
> los tres prefijos de djoser en vez de todo el árbol.

Probar la config antes de instalarla como servicio — conviene recorrer las
rutas que se pisan, no solo una:

```bash
CFG=$HOME/.cloudflared-rayadito/config.yml
cloudflared tunnel --config $CFG ingress validate
for u in /auth/login /auth/registro /auth/social/callback \
         /auth/users/ /auth/jwt/create/ /auth/o/google-oauth2/ \
         /api/products/ /admin/ /carrito /complete/google-oauth2/; do
  printf '%-28s -> ' "$u"
  cloudflared tunnel --config $CFG ingress rule "https://piedrasdelrayadito.cl$u" \
    | grep -i 'service:'
done
```

**Levantá el túnel recién cuando gunicorn y Next ya estén escuchando.** Un
túnel arriba contra puertos vacíos da 502; contra puertos ocupados por otro
proyecto, da 200 con el sitio equivocado.

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
    --bind 127.0.0.1:8010 --workers 3
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
Environment=NODE_ENV=production PORT=3010
Restart=always

[Install]
WantedBy=multi-user.target
```

El túnel va en su propia unidad, apuntada al `config.yml` de Rayadito. **No
uses `cloudflared service install`**: instala la instancia por defecto, que en
una máquina compartida es la de la otra cuenta.

`/etc/systemd/system/rayadito-tunnel.service`:

```ini
[Unit]
Description=Piedras Rayadito - túnel Cloudflare
After=network-online.target
Wants=network-online.target

[Service]
User=USUARIO
ExecStart=/usr/bin/cloudflared --no-autoupdate tunnel \
    --config /home/USUARIO/.cloudflared-rayadito/config.yml run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now rayadito-api rayadito-web rayadito-tunnel
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

## 11. Entorno de pruebas (`test`)

Todo cambio se prueba en la máquina de test **antes** de llegar a `master`.

**Flujo.** Al abrir o actualizar un PR contra `master`, el workflow
`integrate-test.yml` reconstruye la rama `test` desde `master` y le fusiona la
rama del PR. Ese push a `test` dispara `deploy-test.yml`, que corre en el
runner self-hosted y ejecuta `scripts/deploy-test.sh`. El PR **no** se toca: el
merge a `master` lo sigue haciendo el usuario.

`test` se reconstruye desde `master` en cada corrida, así que refleja un solo
PR a la vez — el último que se abrió o actualizó. Es a propósito: evita que se
acumulen ramas viejas y conflictos de PR ya cerrados.

**Seguridad.** Este repo es **público** y el runner es self-hosted. Por eso
`deploy-test.yml` se dispara solo con `push` a `test` (que exige permiso de
escritura) y con `workflow_dispatch`, nunca con `pull_request`;
`integrate-test.yml` corre en runner de GitHub y se salta los PR desde forks.
Sin eso, cualquiera podría ejecutar código arbitrario en la máquina de test.

**Máquina.** El checkout permanente vive en `/mnt/datos/RayaditoEcomerce` con
su propio `.env` (`DEBUG=true`, credenciales propias, MercadoPago vacío —
**nunca** el token de producción). Python 3.12 viene de `uv`, instalado bajo
`~/.local`, sin tocar paquetes del sistema. PostgreSQL corre con el
`docker-compose.yml` del repo. Logs en `/mnt/datos/rayadito-logs/`.

El deploy corre migraciones, `collectstatic`, la suite de tests del backend y
el build de Next; si algo falla, el job queda rojo y los servicios anteriores
siguen arriba.

## Pendientes de esta fase

- **Correo real:** hoy `EMAIL_BACKEND` es `console.EmailBackend` y los mails no
  se envían. Requiere dominio + casilla (Zoho/Google Workspace).
- **Legal Chile:** botón de arrepentimiento, boleta/factura, y revisar el
  contenido de `/terminos` y `/privacidad`.
- **Rotar la contraseña de la base de datos**: la que se usó hasta la Fase 0
  quedó en el historial de git de este repo, que es publico. Ver `docs/ROADMAP.md`.

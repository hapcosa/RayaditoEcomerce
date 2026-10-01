# Publicar productos en Instagram

La app admin tiene un bloque **Instagram** en la ficha de cada producto. Desde ahí
se publica la joya en la cuenta de la tienda, con sus fotos, nombre, descripción,
precio, enlace y hashtags, ya sea de inmediato o programada para más tarde.

Solo se usa la **API oficial de Meta** (Instagram Content Publishing). No hay
scraping, automatización de navegador ni cuentas secundarias.

## Cómo funciona

1. En la app, "Publicar en Instagram" muestra el texto sugerido (editable) y
   los horarios disponibles: ahora, hoy a las 20:00 o mañana.
2. El backend guarda una `InstagramPost` programada (`social/models.py`).
3. Un timer de systemd corre `manage.py publish_instagram` cada 5 minutos y
   publica lo que ya venció. Por eso "Publicar" tarda unos minutos.
4. Al terminar llega un push a la app ("Publicado en Instagram" o el error).

Detalles:

- **Fotos:** se publica la foto principal más la galería, hasta 10 fotos. Con
  más de una foto se arma un carrusel. Instagram solo acepta JPEG con una
  proporción entre 4:5 y 1.91:1, así que el backend convierte cada foto y, si
  queda fuera de rango, le **agrega margen blanco**, nunca la recorta. Para
  controlar el encuadre, recorta la foto en la app antes de publicar.
- **Instagram descarga las fotos desde nuestro servidor**, así que
  `BACKEND_BASE_URL` debe ser el dominio público con HTTPS. Las copias JPEG
  quedan en `public/instagram/<id>/`.
- **Reintentos:** si falla antes de publicarse (token vencido, red caída), se
  reintenta en las 2 corridas siguientes y después queda como "Fallida".
- **No se duplica:** si una corrida muere a mitad de camino, la publicación
  queda "Fallida" con un aviso para revisar el perfil, y no se reintenta sola.
  Un post repetido se ve peor que uno que falta.
- Solo se pueden publicar productos en estado **Publicado**. Si no, el enlace
  de la tienda llevaría a una página que no existe.

## Conectar la cuenta (una vez)

Necesitas:

- La cuenta de Instagram de la tienda como cuenta **profesional** (empresa o
  creador): Instagram → Configuración → Tipo de cuenta.
- Una app en [Meta for Developers](https://developers.facebook.com/apps) con el
  producto **Instagram** y la opción *API setup with Instagram login*. No hace
  falta una página de Facebook.

Pasos:

1. En la app de Meta, ve a *Instagram → API setup with Instagram login* y agrega
   la cuenta de la tienda en "Generate access tokens". Los permisos son
   `instagram_business_basic` e `instagram_business_content_publish`.
2. Copia el **token** que se genera (es de larga duración: 60 días) y el
   **Instagram user id** que aparece junto a la cuenta.
3. Agrega en el `.env` del servidor:

   ```env
   INSTAGRAM_USER_ID=1784...
   INSTAGRAM_ACCESS_TOKEN=IGAA...
   BACKEND_BASE_URL=https://piedrasdelrayadito.cl
   FRONTEND_BASE_URL=https://piedrasdelrayadito.cl
   INSTAGRAM_HASHTAGS=#PiedrasRayadito,#Chiloe,#JoyeriaArtesanal,#HechoAMano
   ```

4. Reinicia `rayadito-api` y activa el timer (ver abajo).

Mientras la app de Meta esté en modo desarrollo, solo puede publicar en las
cuentas agregadas como testers o administradores de esa app. Para publicar en
la cuenta propia de la tienda eso basta: no hace falta pasar por App Review.

Con una cuenta conectada por Facebook Login (página de Facebook más token de
usuario del sistema de Business Manager), se usa
`INSTAGRAM_GRAPH_HOST=graph.facebook.com`. El resto queda igual.

### Renovar el token

> **Pendiente de automatizar.** El token de Instagram Login vence a los 60 días.
> Hay que renovarlo antes del vencimiento y reemplazarlo en el `.env`:
>
> ```bash
> curl -s "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=$INSTAGRAM_ACCESS_TOKEN"
> ```
>
> Después hay que reiniciar `rayadito-api`. Si vence, las publicaciones fallan
> con `code 190` y llega el push de error. El token de un usuario del sistema
> (opción Facebook Login) no vence.

## Timer de systemd

`/etc/systemd/system/rayadito-instagram.service`:

```ini
[Unit]
Description=Publicaciones programadas de Instagram de Piedras Rayadito

[Service]
Type=oneshot
User=USUARIO
WorkingDirectory=/home/USUARIO/rayadito
EnvironmentFile=/home/USUARIO/rayadito/.env
ExecStart=/home/USUARIO/rayadito/.venv/bin/python manage.py publish_instagram
```

`/etc/systemd/system/rayadito-instagram.timer`:

```ini
[Unit]
Description=Revisión de publicaciones de Instagram cada 5 minutos

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now rayadito-instagram.timer
.venv/bin/python manage.py publish_instagram --dry-run   # qué está pendiente
journalctl -u rayadito-instagram -n 50                  # qué pasó en las últimas corridas
```

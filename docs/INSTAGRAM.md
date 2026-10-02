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
   BACKEND_BASE_URL=https://piedrasdelrayadito.cl
   FRONTEND_BASE_URL=https://piedrasdelrayadito.cl
   INSTAGRAM_HASHTAGS=#PiedrasRayadito,#Chiloe,#JoyeriaArtesanal,#HechoAMano
   ```

4. Carga el token en la base (ver "El token vive en la base" abajo), reinicia
   `rayadito-api` y activa los timers.

Mientras la app de Meta esté en modo desarrollo, solo puede publicar en las
cuentas agregadas como testers o administradores de esa app. Para publicar en
la cuenta propia de la tienda eso basta: no hace falta pasar por App Review.

Con una cuenta conectada por Facebook Login (página de Facebook más token de
usuario del sistema de Business Manager), se usa
`INSTAGRAM_GRAPH_HOST=graph.facebook.com`. El resto queda igual.

### El token vive en la base y se renueva solo

El token de Instagram Login vence a los 60 días. Por eso no va en el `.env`:
se guarda **cifrado en la base** (clave derivada de `SECRET_KEY`) y
`manage.py instagram_token refresh` lo renueva, una vez al día desde su timer,
cuando le quedan 15 días o menos. Así un dump de la base —los backups se copian
fuera del servidor— no lleva un token usable.

Cargarlo por primera vez (se lee por stdin para que no quede en el historial
del shell ni a la vista en `ps`):

```bash
cd ~/servicios/RayaditoEcomerce
.venv/bin/python manage.py instagram_token set --expires-in-days 60   # pega el token y Ctrl-D
# o, si ya estaba en el .env:
.venv/bin/python manage.py instagram_token set --from-env
.venv/bin/python manage.py instagram_token status
```

Después se puede borrar `INSTAGRAM_ACCESS_TOKEN` del `.env`: mientras haya
token en la base, ese no se usa. No hace falta reiniciar `rayadito-api`, porque
el token se lee de la base en cada publicación.

Reglas de Meta ([referencia](https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token/)):
solo se renueva un token con **al menos 24 horas** de antigüedad que **no haya
vencido**, y cada renovación da 60 días desde ese momento. **Un token vencido ya
no se puede renovar**: hay que generar otro en el panel de Meta y volver a
cargarlo con `set`. Por eso el comando renueva con 15 días de margen. Si falla,
el error queda en `/admin/social/instagramtoken/`, llega un push al staff y el
timer queda en estado *failed* en `systemctl list-timers`. Al día siguiente lo
reintenta.

Si cambia `SECRET_KEY`, el token guardado ya no se puede descifrar: `status`
lo avisa y hay que volver a cargarlo.

El token de un usuario del sistema (opción Facebook Login,
`INSTAGRAM_GRAPH_HOST=graph.facebook.com`) no vence, y `refresh` no lo toca.

`/etc/systemd/system/rayadito-instagram-token.service`:

```ini
[Unit]
Description=Renovacion del token de Instagram de Piedras Rayadito

[Service]
Type=oneshot
User=donaldchavez
WorkingDirectory=/home/donaldchavez/servicios/RayaditoEcomerce
ExecStart=/home/donaldchavez/servicios/RayaditoEcomerce/.venv/bin/python manage.py instagram_token refresh
```

`/etc/systemd/system/rayadito-instagram-token.timer`:

```ini
[Unit]
Description=Revision diaria del vencimiento del token de Instagram

[Timer]
OnCalendar=*-*-* 04:10:00
Persistent=true

[Install]
WantedBy=timers.target
```

Sin token en la base el comando no hace nada y termina bien, así que el timer
se puede instalar antes de conectar Instagram.

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

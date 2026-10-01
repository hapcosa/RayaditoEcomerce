"""Publicacion de productos en Instagram: texto, fotos y la corrida del comando.

Una publicacion fallida nunca reintenta a ciegas si existe la posibilidad de
que ya haya salido: un post duplicado en el perfil de la tienda es peor que uno
que falta, porque el que falta se arregla tocando un boton.
"""
import io
import logging
import re
import time
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import F
from django.utils import timezone
from django.utils.html import strip_tags
from PIL import Image, ImageOps

from notifications.formatting import clp

from . import instagram
from .models import InstagramPost

logger = logging.getLogger(__name__)

# Limites de Instagram para el texto de una publicacion.
CAPTION_MAX_CHARS = 2200
HASHTAG_MAX = 30
DESCRIPTION_MAX_CHARS = 1200

# Proporcion aceptada por Instagram para fotos del feed: de 4:5 (vertical) a
# 1.91:1 (horizontal). Fuera de eso rechaza la foto entera.
MIN_RATIO = 4 / 5
MAX_RATIO = 1.91
MAX_WIDTH = 1440
PAD_COLOR = (255, 255, 255)

# Reintentos de una publicacion que fallo antes de llegar a publicarse (token
# vencido, foto que Meta no pudo descargar, red caida).
MAX_ATTEMPTS = 3
# Una publicacion que lleva mas que esto en PUBLISHING es de una corrida que
# murio: el comando nunca tarda tanto (ver instagram.POLL_MAX_TRIES).
STUCK_AFTER = timedelta(minutes=30)
# Tope por corrida: el limite de Meta es de 50 publicaciones por cuenta cada 24 h
# y el timer corre cada pocos minutos.
BATCH_SIZE = 5


def product_url(product):
    base = (settings.FRONTEND_BASE_URL or '').rstrip('/')
    if not base or not product.slug:
        return ''
    return f'{base}/productos/{product.slug}'


def _plain_description(text):
    text = strip_tags(text or '')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if len(text) > DESCRIPTION_MAX_CHARS:
        text = text[:DESCRIPTION_MAX_CHARS].rsplit(' ', 1)[0] + '…'
    return text


def build_caption(product):
    """Texto sugerido para la publicacion. La app lo muestra editable."""
    parts = [product.name]
    description = _plain_description(product.description)
    if description:
        parts.append(description)
    # Dinero en entero CLP (ver AGENTS.md); clp() es solo presentacion.
    parts.append(f'${clp(product.price)}')
    link = product_url(product)
    if link:
        # Instagram no hace clickeables los links del texto, pero copiarlo
        # sigue siendo mas facil que buscar el producto en la tienda.
        parts.append(f'Disponible en {link}')
    hashtags = [tag for tag in settings.INSTAGRAM_HASHTAGS if tag.strip()][:HASHTAG_MAX]
    if hashtags:
        parts.append(' '.join(hashtags))
    return '\n\n'.join(parts)[:CAPTION_MAX_CHARS]


def product_photos(product):
    """Foto principal + galeria, en el orden en que se ven en la tienda."""
    photos = [product.photo] if product.photo else []
    photos += [
        image.photos for image in product.galleryproduct_set.order_by('id')
        if image.photos
    ]
    return photos[:instagram.MAX_CAROUSEL_ITEMS]


def _to_instagram_jpeg(field_file):
    """JPEG que Instagram acepta: RGB, ancho acotado y proporcion permitida.

    Una foto fuera de proporcion se completa con margen blanco en vez de
    recortarse: el recorte lo decide la duena desde la app, no este codigo.
    """
    with field_file.open('rb') as handle:
        image = Image.open(handle)
        image = ImageOps.exif_transpose(image).convert('RGB')

    width, height = image.size
    ratio = width / height
    if ratio < MIN_RATIO:
        canvas = Image.new('RGB', (round(height * MIN_RATIO), height), PAD_COLOR)
        canvas.paste(image, ((canvas.width - width) // 2, 0))
        image = canvas
    elif ratio > MAX_RATIO:
        canvas = Image.new('RGB', (width, round(width / MAX_RATIO)), PAD_COLOR)
        canvas.paste(image, (0, (canvas.height - height) // 2))
        image = canvas

    if image.width > MAX_WIDTH:
        image = image.resize(
            (MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)),
            Image.LANCZOS,
        )

    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    return buffer.getvalue()


def _public_url(name):
    url = default_storage.url(name)
    if url.startswith(('http://', 'https://')):
        return url
    base = (settings.BACKEND_BASE_URL or '').rstrip('/')
    if not base:
        raise instagram.InstagramError(
            'falta BACKEND_BASE_URL: Instagram necesita descargar las fotos '
            'desde una URL publica')
    return f'{base}{url}'


def prepare_images(post):
    """Copia las fotos del producto como JPEG publicos y devuelve sus URLs."""
    photos = product_photos(post.product)
    if not photos:
        raise instagram.InstagramError('el producto no tiene fotos para publicar')
    urls = []
    for index, photo in enumerate(photos, start=1):
        name = default_storage.save(
            f'instagram/{post.pk}/{index}.jpg',
            ContentFile(_to_instagram_jpeg(photo)),
        )
        urls.append(_public_url(name))
    return urls


def _push(title, body, post):
    # Import tardio: social no debe depender de notifications para cargar, y
    # un push que falla no cambia el resultado de la publicacion.
    from notifications.services import push_admins
    try:
        push_admins(title=title, body=body, data={
            'type': 'instagram_post', 'product_id': post.product_id,
            'post_id': post.pk,
        })
    except Exception:
        logger.exception('no se pudo pushear el aviso de Instagram %s', post.pk)


def due_posts(now=None):
    now = now or timezone.now()
    return (
        InstagramPost.objects
        .filter(status=InstagramPost.Status.SCHEDULED, scheduled_for__lte=now)
        .select_related('product')
        .order_by('scheduled_for', 'id')
    )


def recover_stuck_posts(now=None):
    """Marca como fallidas las publicaciones de una corrida que murio.

    No se reintentan solas: si la corrida murio despues de `media_publish`, la
    foto ya esta en Instagram y reintentar la duplicaria.
    """
    now = now or timezone.now()
    return InstagramPost.objects.filter(
        status=InstagramPost.Status.PUBLISHING,
        started_at__lt=now - STUCK_AFTER,
    ).update(
        status=InstagramPost.Status.FAILED,
        last_error='La publicación quedó a medio camino. Revisa el perfil de '
                   'Instagram antes de volver a publicarla, puede que ya haya salido.',
    )


def _claim(post, now):
    """Toma la publicacion para esta corrida. False si otra ya la tomo."""
    return bool(
        InstagramPost.objects
        .filter(pk=post.pk, status=InstagramPost.Status.SCHEDULED)
        .update(status=InstagramPost.Status.PUBLISHING, started_at=now,
                attempts=F('attempts') + 1)
    )


def publish_post(post, now=None, sleep=time.sleep):
    """Publica una publicacion programada. Devuelve True si salio."""
    now = now or timezone.now()
    if not _claim(post, now):
        return False
    post.refresh_from_db()

    try:
        urls = prepare_images(post)
        media_id, permalink = instagram.publish_images(urls, post.caption, sleep=sleep)
    except Exception as exc:
        # Ancho a proposito: cualquier falla antes de `media_publish` deja la
        # publicacion sin salir, y lo correcto es reintentarla o reportarla.
        if not isinstance(exc, instagram.InstagramError):
            logger.exception('error inesperado publicando %s en Instagram', post.pk)
        post.last_error = str(exc)[:2000]
        if post.attempts >= MAX_ATTEMPTS:
            post.status = InstagramPost.Status.FAILED
            post.save(update_fields=['status', 'last_error'])
            _push('No se pudo publicar en Instagram',
                  f'{post.product.name}: {post.last_error[:120]}', post)
        else:
            post.status = InstagramPost.Status.SCHEDULED
            post.save(update_fields=['status', 'last_error'])
        logger.warning('publicacion %s fallo (intento %s): %s',
                       post.pk, post.attempts, post.last_error)
        return False

    post.status = InstagramPost.Status.PUBLISHED
    post.media_id = media_id
    post.permalink = permalink
    post.published_at = timezone.now()
    post.last_error = ''
    post.save(update_fields=['status', 'media_id', 'permalink',
                             'published_at', 'last_error'])
    _push('Publicado en Instagram', post.product.name, post)
    return True

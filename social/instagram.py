"""Cliente minimo de la API oficial de Instagram (Content Publishing).

Solo lo que hace falta para publicar fotos propias de la tienda: crear el
contenedor de cada foto, esperar a que Meta lo procese y publicarlo. Sin SDK,
como `notifications/expo.py`: son unos pocos requests.

Por defecto apunta a graph.instagram.com ("Instagram API with Instagram
Login"), que no necesita una pagina de Facebook. Con una cuenta conectada via
Facebook Login se cambia INSTAGRAM_GRAPH_HOST a graph.facebook.com; los
endpoints son los mismos.

https://developers.facebook.com/docs/instagram-platform/content-publishing
"""
import logging
import time

import requests
from django.conf import settings

from . import tokens

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 20
# Instagram descarga y procesa cada foto por su cuenta; publicar antes de que
# el contenedor quede FINISHED devuelve error. Con fotos normales tarda pocos
# segundos.
POLL_INTERVAL_SECONDS = 3
POLL_MAX_TRIES = 20
# Limite de Instagram para un carrusel.
MAX_CAROUSEL_ITEMS = 10


class InstagramError(Exception):
    """Meta rechazo el request, no respondio o el contenedor fallo."""


def is_configured():
    return bool(settings.INSTAGRAM_USER_ID and tokens.access_token())


def _url(path):
    host = settings.INSTAGRAM_GRAPH_HOST.rstrip('/')
    return f'https://{host}/{settings.INSTAGRAM_GRAPH_VERSION}/{path}'


def _scrub(text):
    # El token viaja como parametro y `requests` lo incluye en los mensajes de
    # error de red. Nunca debe terminar en un log ni en la base.
    token = tokens.access_token()
    return text.replace(token, '***') if token else text


def _request(method, path, params):
    params = {**params, 'access_token': tokens.access_token()}
    try:
        if method == 'GET':
            response = requests.get(_url(path), params=params, timeout=TIMEOUT_SECONDS)
        else:
            response = requests.post(_url(path), data=params, timeout=TIMEOUT_SECONDS)
        payload = response.json()
    except Exception as exc:
        raise InstagramError(_scrub(f'sin respuesta de Instagram: {exc}')) from None

    if 'error' in payload:
        error = payload['error'] or {}
        message = error.get('error_user_msg') or error.get('message') or 'error'
        raise InstagramError(_scrub(f'{message} (code {error.get("code")})'))
    if response.status_code >= 400:
        raise InstagramError(f'Instagram respondio HTTP {response.status_code}')
    return payload


def _create_container(params):
    payload = _request('POST', f'{settings.INSTAGRAM_USER_ID}/media', params)
    container_id = payload.get('id')
    if not container_id:
        raise InstagramError(f'respuesta sin id al crear el contenedor: {payload}')
    return container_id


def _wait_until_ready(container_id, sleep=time.sleep):
    for _ in range(POLL_MAX_TRIES):
        payload = _request('GET', container_id, {'fields': 'status_code,status'})
        code = payload.get('status_code')
        if code == 'FINISHED':
            return
        if code in ('ERROR', 'EXPIRED'):
            raise InstagramError(
                f'Instagram no pudo procesar la foto: {payload.get("status") or code}')
        sleep(POLL_INTERVAL_SECONDS)
    raise InstagramError('Instagram tardo demasiado en procesar las fotos')


def publish_images(image_urls, caption, sleep=time.sleep):
    """Publica una foto o un carrusel y devuelve `(media_id, permalink)`.

    `image_urls` son URLs HTTPS publicas de JPEG: Instagram las descarga desde
    sus servidores, no recibe el archivo. El permalink puede venir vacio si
    Meta no lo entrega; la publicacion ya existe igual.
    """
    image_urls = list(image_urls)[:MAX_CAROUSEL_ITEMS]
    if not image_urls:
        raise InstagramError('el producto no tiene fotos para publicar')

    if len(image_urls) == 1:
        container_id = _create_container(
            {'image_url': image_urls[0], 'caption': caption})
    else:
        children = [
            _create_container({'image_url': url, 'is_carousel_item': 'true'})
            for url in image_urls
        ]
        for child in children:
            _wait_until_ready(child, sleep=sleep)
        container_id = _create_container({
            'media_type': 'CAROUSEL',
            'children': ','.join(children),
            'caption': caption,
        })
    _wait_until_ready(container_id, sleep=sleep)

    payload = _request('POST', f'{settings.INSTAGRAM_USER_ID}/media_publish',
                       {'creation_id': container_id})
    media_id = payload.get('id')
    if not media_id:
        raise InstagramError(f'respuesta sin id al publicar: {payload}')

    try:
        permalink = _request('GET', media_id, {'fields': 'permalink'}).get('permalink', '')
    except InstagramError:
        logger.warning('publicado %s pero no se pudo leer el permalink', media_id)
        permalink = ''
    return media_id, permalink

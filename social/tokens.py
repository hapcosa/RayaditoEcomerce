"""Token de acceso de Instagram: guardado cifrado en la base y renovacion.

El token de "Instagram API with Instagram Login" dura 60 dias. Meta lo renueva
por otros 60 con `GET graph.instagram.com/refresh_access_token`, siempre que
tenga al menos 24 horas y no haya vencido; uno vencido ya no se puede renovar
y hay que generar otro a mano en el panel de Meta.
https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token/

El token de usuario del sistema de Business Manager (opcion Facebook Login,
INSTAGRAM_GRAPH_HOST=graph.facebook.com) no vence: ahi no se renueva nada.
"""
import base64
import logging
from datetime import timedelta

import requests
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings
from django.utils import timezone

from .models import InstagramToken

logger = logging.getLogger(__name__)

REFRESH_URL = 'https://graph.instagram.com/refresh_access_token'
TIMEOUT_SECONDS = 20
# Meta rechaza renovar un token con menos de 24 h.
MIN_AGE = timedelta(hours=24)
# Se renueva con este margen antes del vencimiento: con un timer diario quedan
# dos semanas de reintentos si Meta o la red fallan.
REFRESH_BEFORE = timedelta(days=15)


class TokenError(Exception):
    pass


def _fernet():
    key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=b'rayadito instagram access token',
    ).derive(settings.SECRET_KEY.encode())
    return Fernet(base64.urlsafe_b64encode(key))


def _row():
    return InstagramToken.objects.filter(pk=1).first()


def access_token():
    """El token vigente: el de la base y, si no hay, el del `.env`.

    El del `.env` queda como respaldo para la transicion: apenas se carga con
    `instagram_token set` (o `--from-env`) manda el de la base.
    """
    row = _row()
    if row is not None:
        try:
            return _fernet().decrypt(row.encrypted_token.encode()).decode()
        except InvalidToken:
            # Cambio SECRET_KEY: el token guardado ya no se puede leer.
            logger.error('El token de Instagram guardado no se puede descifrar '
                         '(¿cambio SECRET_KEY?). Vuelve a cargarlo con instagram_token set.')
            return ''
    return settings.INSTAGRAM_ACCESS_TOKEN


def save_token(token, *, expires_in=None, now=None):
    now = now or timezone.now()
    token = (token or '').strip()
    if not token:
        raise TokenError('token vacio')
    InstagramToken.objects.update_or_create(pk=1, defaults={
        'encrypted_token': _fernet().encrypt(token.encode()).decode(),
        'issued_at': now,
        'expires_at': now + timedelta(seconds=int(expires_in)) if expires_in else None,
        'last_error': '',
    })


def refreshable():
    """Solo los tokens de Instagram Login vencen y se renuevan."""
    return settings.INSTAGRAM_GRAPH_HOST.rstrip('/') == 'graph.instagram.com'


def is_due(row, now):
    if now - row.issued_at < MIN_AGE:
        return False
    # Sin vencimiento conocido (cargado a mano) se renueva: asi se aprende.
    return row.expires_at is None or row.expires_at - now <= REFRESH_BEFORE


def refresh(*, now=None, force=False):
    """Renueva el token si toca. Devuelve True si lo renovo.

    Lanza TokenError si Meta lo rechaza o no responde; el error queda en la
    fila para verlo en /admin/.
    """
    now = now or timezone.now()
    row = _row()
    if row is None:
        raise TokenError('no hay token guardado: cárgalo con `instagram_token set`')
    if not refreshable():
        return False
    if not force and not is_due(row, now):
        return False
    if now - row.issued_at < MIN_AGE:
        raise TokenError('Meta solo renueva tokens con al menos 24 horas')

    token = access_token()
    row.last_refresh_attempt = now
    try:
        response = requests.get(REFRESH_URL, params={
            'grant_type': 'ig_refresh_token', 'access_token': token,
        }, timeout=TIMEOUT_SECONDS)
        payload = response.json()
    except Exception as exc:
        error = f'sin respuesta de Instagram: {exc.__class__.__name__}'
    else:
        if 'error' in payload or not payload.get('access_token'):
            detail = payload.get('error') or {}
            error = f"{detail.get('message') or 'respuesta sin token'} (code {detail.get('code')})"
        else:
            save_token(payload['access_token'], expires_in=payload.get('expires_in'), now=now)
            InstagramToken.objects.filter(pk=1).update(last_refresh_attempt=now)
            return True

    error = error.replace(token, '***') if token else error
    row.last_error = error
    row.save(update_fields=['last_refresh_attempt', 'last_error', 'updated_at'])
    raise TokenError(error)

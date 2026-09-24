"""Cliente minimo de la Expo Push API.

Expo recibe los mensajes y se los pasa a FCM/APNs. No hay SDK en el proyecto:
es un POST a un endpoint, y una dependencia menos que mantener.

https://docs.expo.dev/push-notifications/sending-notifications/
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'
# Expo acepta hasta 100 mensajes por request.
CHUNK_SIZE = 100
TIMEOUT_SECONDS = 10


def _headers():
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
    }
    # Opcional: si la cuenta Expo tiene activado "enhanced security", sin este
    # token los envios se rechazan.
    if settings.EXPO_ACCESS_TOKEN:
        headers['authorization'] = f'Bearer {settings.EXPO_ACCESS_TOKEN}'
    return headers


def _chunks(items):
    for start in range(0, len(items), CHUNK_SIZE):
        yield items[start:start + CHUNK_SIZE]


def send_messages(messages):
    """Manda los mensajes y devuelve los tickets, uno por mensaje y en orden.

    Un ticket es `{'status': 'ok', 'id': ...}` o
    `{'status': 'error', 'message': ..., 'details': {'error': 'DeviceNotRegistered'}}`.
    Si el request falla entero devuelve un ticket de error por cada mensaje, para
    que quien llama no tenga que distinguir entre "fallo la red" y "fallo este
    aparato".
    """
    if not messages:
        return []

    tickets = []
    for chunk in _chunks(messages):
        try:
            response = requests.post(
                EXPO_PUSH_URL, json=chunk, headers=_headers(),
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.exception('fallo el envio a Expo Push')
            tickets.extend(
                {'status': 'error', 'message': str(exc), 'details': {}}
                for _ in chunk
            )
            continue

        data = payload.get('data')
        if not isinstance(data, list) or len(data) != len(chunk):
            logger.error('respuesta inesperada de Expo Push: %s', payload)
            tickets.extend(
                {'status': 'error', 'message': 'respuesta inesperada de Expo',
                 'details': {}}
                for _ in chunk
            )
            continue
        tickets.extend(data)
    return tickets

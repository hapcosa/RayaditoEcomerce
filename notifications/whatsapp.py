"""Cliente minimo de la WhatsApp Cloud API (API oficial de Meta).

Solo manda plantillas aprobadas: un aviso que inicia la tienda, fuera de una
conversacion abierta por el cliente, tiene que ir como plantilla. Sin SDK, como
`notifications/expo.py` y `social/instagram.py`.

https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/utility-templates/utility-templates
"""
import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15
GRAPH_HOST = 'graph.facebook.com'


class WhatsAppError(Exception):
    """Meta rechazo el mensaje o no respondio."""


def is_enabled():
    """Apagado salvo que este el flag y las dos credenciales."""
    return bool(
        settings.WHATSAPP_ENABLED
        and settings.WHATSAPP_PHONE_NUMBER_ID
        and settings.WHATSAPP_ACCESS_TOKEN
    )


def normalize_phone(raw):
    """Celular chileno en el formato que pide Meta: '569XXXXXXXX', sin '+'.

    Acepta lo que escribe la gente en el checkout ('9 1234 5678',
    '+56 9 1234 5678', '56912345678'). Devuelve '' si no es un celular chileno:
    la tienda despacha solo dentro de Chile y un numero mal escrito es un aviso
    que le llega a otra persona.
    """
    digits = re.sub(r'\D', '', raw or '')
    if len(digits) == 9:
        digits = f'56{digits}'
    if len(digits) == 11 and digits.startswith('569'):
        return digits
    return ''


def _scrub(text):
    token = settings.WHATSAPP_ACCESS_TOKEN
    return text.replace(token, '***') if token else text


def send_template(to, template, parameters, language=None):
    """Manda una plantilla con parametros con nombre. Devuelve el wamid.

    `parameters` es un dict {'nombre': 'Ana', 'pedido': '123'}; los nombres
    tienen que ser los mismos que los `{{nombre}}` de la plantilla aprobada en
    Meta, si no Meta rechaza el envio (codigo 132000).
    """
    url = (f'https://{GRAPH_HOST}/{settings.WHATSAPP_GRAPH_VERSION}/'
           f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages')
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': to,
        'type': 'template',
        'template': {
            'name': template,
            'language': {'code': language or settings.WHATSAPP_TEMPLATE_LANGUAGE},
        },
    }
    if parameters:
        payload['template']['components'] = [{
            'type': 'body',
            'parameters': [
                {'type': 'text', 'parameter_name': name, 'text': str(value)}
                for name, value in parameters.items()
            ],
        }]

    try:
        response = requests.post(
            url, json=payload, timeout=TIMEOUT_SECONDS,
            headers={'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}'},
        )
        data = response.json()
    except Exception as exc:
        raise WhatsAppError(_scrub(f'sin respuesta de WhatsApp: {exc}')) from None

    if 'error' in data:
        error = data['error'] or {}
        details = (error.get('error_data') or {}).get('details') or ''
        message = error.get('message') or 'error'
        raise WhatsAppError(_scrub(
            f'{message} (code {error.get("code")}){": " + details if details else ""}'))
    if response.status_code >= 400:
        raise WhatsAppError(f'WhatsApp respondio HTTP {response.status_code}')

    messages = data.get('messages') or []
    if not messages or not messages[0].get('id'):
        raise WhatsAppError(f'respuesta inesperada de WhatsApp: {data}')
    return messages[0]['id']

"""Avisos al cliente por WhatsApp: pedido pagado y pedido despachado.

Mismas reglas que `services.py`: un aviso nunca tumba la operacion que lo
dispara (sale en `transaction.on_commit` y cualquier error se registra y se
traga), y sin `WHATSAPP_ENABLED` no se hace nada.

Solo se le escribe a quien lo acepto en el checkout (`WhatsAppOptIn`). Las
plantillas tienen que existir y estar aprobadas en Meta con estos nombres y
parametros; ver docs/WHATSAPP.md.
"""
import logging

from django.db import IntegrityError, transaction

from . import whatsapp
from .formatting import clp
from .models import WhatsAppMessage, WhatsAppOptIn

logger = logging.getLogger(__name__)

# Nombre en Meta -> parametros con nombre del cuerpo de la plantilla.
TEMPLATE_PAID_ORDER = 'pedido_confirmado'    # nombre, pedido, total
TEMPLATE_SHIPPED = 'pedido_despachado'       # nombre, pedido, envio, seguimiento


def record_opt_in(order, phone, consent_text):
    """Guarda el consentimiento del checkout. None si el telefono no sirve."""
    normalized = whatsapp.normalize_phone(phone)
    if not normalized:
        return None
    opt_in, _ = WhatsAppOptIn.objects.update_or_create(
        order=order,
        defaults={'phone': normalized, 'consent_text': consent_text,
                  'revoked_at': None},
    )
    return opt_in


def _first_name(order):
    return (order.full_name or '').strip().split(' ')[0] or 'Hola'


def _reference(order):
    # El numero que ve el cliente en /pedidos.
    return order.transaction_id or str(order.id)


def send_order_notice(order, key, template, parameters):
    """Manda el aviso `key` del pedido una sola vez. Devuelve True si salio."""
    if not whatsapp.is_enabled():
        return False
    opt_in = WhatsAppOptIn.objects.filter(order=order, revoked_at__isnull=True).first()
    if opt_in is None:
        return False

    # Se reserva el aviso antes de llamar a Meta: si MercadoPago reenvia la
    # aprobacion mientras el primer envio esta en curso, el segundo choca con
    # la restriccion unica y no manda (ni cobra) un duplicado.
    try:
        with transaction.atomic():
            message = WhatsAppMessage.objects.create(
                order=order, key=key, template=template, to=opt_in.phone)
    except IntegrityError:
        logger.info('aviso de WhatsApp %s del pedido %s ya enviado', key, order.id)
        return False

    try:
        message.wamid = whatsapp.send_template(opt_in.phone, template, parameters)
        message.status = WhatsAppMessage.Status.SENT
    except Exception as exc:
        # Ancho a proposito, como en `services.send_admin_mail`.
        logger.exception('no se pudo enviar el WhatsApp %s del pedido %s', key, order.id)
        message.status = WhatsAppMessage.Status.FAILED
        message.error = str(exc)[:500]
    message.save(update_fields=['wamid', 'status', 'error', 'updated_at'])
    return message.status == WhatsAppMessage.Status.SENT


def notify_paid_order(order):
    return send_order_notice(order, 'paid_order', TEMPLATE_PAID_ORDER, {
        'nombre': _first_name(order),
        'pedido': _reference(order),
        'total': f'${clp(order.amount)}',
    })


def notify_shipped(order):
    shipping = order.shipping_id
    return send_order_notice(order, 'shipped', TEMPLATE_SHIPPED, {
        'nombre': _first_name(order),
        'pedido': _reference(order),
        'envio': shipping.name if shipping else 'el courier',
        'seguimiento': order.deliveryNumber or '-',
    })


def _safely(notice, order):
    # Un callback de `on_commit` que revienta propaga la excepcion a quien
    # commiteo: el webhook de MercadoPago responderia 500 por un aviso.
    try:
        notice(order)
    except Exception:
        logger.exception('fallo el aviso de WhatsApp del pedido %s', order.id)


def notify_paid_order_on_commit(order):
    transaction.on_commit(lambda: _safely(notify_paid_order, order))


def notify_shipped_on_commit(order):
    transaction.on_commit(lambda: _safely(notify_shipped, order))

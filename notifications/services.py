"""Avisos al administrador: correo y push a la app.

Un aviso nunca puede tumbar la operacion que lo dispara: el correo sale despues
de que la transaccion commitea (`transaction.on_commit`) y cualquier error del
servidor SMTP se registra y se traga. Si el webhook de MercadoPago reventara
por no poder mandar un mail, MercadoPago reintentaria la notificacion y
terminaria deshabilitando el endpoint.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string

from orders.models import OrderItem

from . import expo
from .formatting import clp
from .models import DevicePushToken

logger = logging.getLogger(__name__)


def admin_recipients():
    """Correos del dueno. Vacio = avisos apagados (asi esta en desarrollo)."""
    return [address for address in settings.ADMIN_NOTIFY_EMAILS if address.strip()]


def order_admin_url(order):
    """Link a la ficha del pedido en el admin de Django, si hay dominio."""
    base = (settings.BACKEND_BASE_URL or '').rstrip('/')
    if not base:
        return ''
    return f'{base}/admin/orders/order/{order.id}/change/'


def send_admin_mail(subject, template, context):
    recipients = admin_recipients()
    if not recipients:
        logger.info('aviso al admin omitido (ADMIN_NOTIFY_EMAILS vacio): %s', subject)
        return False

    try:
        EmailMessage(
            subject=subject,
            body=render_to_string(template, context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        ).send(fail_silently=False)
    except Exception:
        # A proposito ancho: da igual si fallo la conexion, la autenticacion o
        # el render. El aviso se pierde, la venta no.
        logger.exception('no se pudo enviar el aviso al admin: %s', subject)
        return False
    return True


def push_admins(title, body, data=None):
    """Push a los aparatos del staff. Devuelve a cuantos les llego.

    Un token que Expo declara muerto (`DeviceNotRegistered`: desinstalaron la
    app o revocaron el permiso) se desactiva solo, para no arrastrar destinos
    que nunca van a responder.
    """
    tokens = list(
        DevicePushToken.objects
        .filter(is_active=True, user__is_staff=True)
        .order_by('id')
    )
    if not tokens:
        logger.info('push omitido (ningun aparato registrado): %s', title)
        return 0

    messages = [
        {
            'to': device.token,
            'title': title,
            'body': body,
            'data': data or {},
            'sound': 'default',
            'priority': 'high',
            # Agrupa los avisos del mismo tipo en la bandeja de Android en vez
            # de apilar una notificacion por venta.
            'channelId': 'ventas',
        }
        for device in tokens
    ]
    tickets = expo.send_messages(messages)

    delivered = 0
    for device, ticket in zip(tokens, tickets):
        if ticket.get('status') == 'ok':
            delivered += 1
            if device.last_error:
                device.last_error = ''
                device.save(update_fields=['last_error', 'updated_at'])
            continue

        error = (ticket.get('details') or {}).get('error', '')
        device.last_error = (error or ticket.get('message') or 'error')[:255]
        update_fields = ['last_error', 'updated_at']
        if error == 'DeviceNotRegistered':
            device.is_active = False
            update_fields.append('is_active')
        device.save(update_fields=update_fields)
        logger.warning('push rechazado para %s: %s', device, device.last_error)
    return delivered


def paid_order_push(order, items):
    """Texto del push de venta. `data` lo lee la app para abrir el pedido."""
    pieces = sum(item.count for item in items)
    who = (order.full_name or '').strip() or 'Sin nombre'
    return {
        'title': f'Venta aprobada — ${clp(order.amount)}',
        'body': f'Pedido #{order.id} · {who} · '
                f'{pieces} {"pieza" if pieces == 1 else "piezas"}',
        'data': {'type': 'paid_order', 'order_id': order.id},
    }


def notify_paid_order(order):
    """Avisa que entro una venta. Lo llama el pago aprobado, una sola vez."""
    items = list(
        OrderItem.objects.select_related('product').filter(order=order)
    )
    context = {
        'order': order,
        'items': items,
        'admin_url': order_admin_url(order),
        'customer_email': order.email or (order.user.email if order.user_id else ''),
    }
    sent = send_admin_mail(
        subject=f'Venta aprobada — pedido #{order.id}',
        template='notifications/admin_paid_order.txt',
        context=context,
    )
    # El push no depende del correo: son dos canales del mismo aviso y cada uno
    # puede fallar por su cuenta.
    try:
        pushed = push_admins(**paid_order_push(order, items))
    except Exception:
        logger.exception('no se pudo pushear el aviso del pedido %s', order.id)
        pushed = 0
    return sent or bool(pushed)


def notify_paid_order_on_commit(order):
    """Programa el aviso para cuando la venta ya este guardada de verdad.

    Dentro de `transaction.atomic()` todavia puede fallar algo posterior y
    volver todo atras; el correo, en cambio, no se puede des-enviar.
    """
    transaction.on_commit(lambda: notify_paid_order(order))

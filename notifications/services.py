"""Avisos al administrador. Hoy solo por correo.

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
    return send_admin_mail(
        subject=f'Venta aprobada — pedido #{order.id}',
        template='notifications/admin_paid_order.txt',
        context=context,
    )


def notify_paid_order_on_commit(order):
    """Programa el aviso para cuando la venta ya este guardada de verdad.

    Dentro de `transaction.atomic()` todavia puede fallar algo posterior y
    volver todo atras; el correo, en cambio, no se puede des-enviar.
    """
    transaction.on_commit(lambda: notify_paid_order(order))

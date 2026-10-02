"""Derecho a retracto: registrar la solicitud y avisar a las dos partes.

Ver `WithdrawalRequest` para por que el formulario no rechaza por fecha.
"""
import logging
import secrets

from django.db import IntegrityError, transaction
from django.db.models import Q

from notifications.services import (
    customer_email, order_admin_url, order_reference, push_admins,
    send_admin_mail, send_customer_mail,
)

from .models import Order, WithdrawalRequest

logger = logging.getLogger(__name__)

OPEN_STATUSES = (WithdrawalRequest.Status.RECEIVED, WithdrawalRequest.Status.ACCEPTED)


def find_order(number, email):
    """Pedido pagado con ese numero y ese correo, o None.

    El cliente ve como numero el id del pago de MercadoPago (`transaction_id`)
    y el dueno ve el id interno; se aceptan los dos. El correo es el que
    desambigua, y si no calza la respuesta es la misma que si el pedido no
    existiera, para no confirmar numeros de pedido a cualquiera.
    """
    number = (number or '').strip().lstrip('#').strip()
    email = (email or '').strip().lower()
    if not number or not email:
        return None
    match = Q(transaction_id=number)
    if number.isdigit():
        match |= Q(id=int(number))
    candidates = (
        Order.objects.filter(match, paid_at__isnull=False)
        .select_related('user', 'shipping_id')
    )
    for order in candidates:
        if customer_email(order).strip().lower() == email:
            return order
    return None


def _new_code(order):
    return f'RET-{order.id}-{secrets.token_hex(2).upper()}'


def create_withdrawal(order, email, reason=''):
    """Registra la solicitud. Devuelve `(solicitud, creada)`.

    Si el pedido ya tiene una abierta se devuelve esa: un doble click o un
    reintento no debe generar dos constancias distintas para el mismo pedido.
    """
    existing = order.withdrawal_requests.filter(status__in=OPEN_STATUSES).first()
    if existing:
        return existing, False

    for _ in range(5):
        try:
            with transaction.atomic():
                withdrawal = WithdrawalRequest.objects.create(
                    order=order, email=email.strip(), reason=reason.strip(),
                    code=_new_code(order),
                )
            break
        except IntegrityError:
            # Choque del sufijo aleatorio con otra solicitud del mismo pedido.
            continue
    else:
        raise RuntimeError(f'no se pudo generar un codigo para el pedido {order.id}')

    transaction.on_commit(lambda: notify_withdrawal(withdrawal))
    return withdrawal, True


def notify_withdrawal(withdrawal):
    order = withdrawal.order
    send_customer_mail(
        to=withdrawal.email,
        subject=f'Recibimos tu solicitud de retracto — {withdrawal.code}',
        template='notifications/customer_withdrawal_received.txt',
        context={'withdrawal': withdrawal, 'reference': order_reference(order)},
    )
    send_admin_mail(
        subject=f'Solicitud de retracto — pedido #{order.id} ({withdrawal.code})',
        template='notifications/admin_withdrawal_request.txt',
        context={'withdrawal': withdrawal, 'order': order,
                 'admin_url': order_admin_url(order)},
    )
    try:
        push_admins(
            title=f'Retracto — pedido #{order.id}',
            body=f'{(order.full_name or "Sin nombre").strip()} · {withdrawal.code}',
            data={'type': 'withdrawal', 'order_id': order.id},
        )
    except Exception:
        logger.exception('no se pudo pushear el retracto %s', withdrawal.code)

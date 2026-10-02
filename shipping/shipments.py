"""Emision de ordenes de flete y seguimiento de pedidos despachados."""
import logging

from django.db import transaction
from django.utils import timezone

from orders.models import Order

from . import starken
from .models import Shipment, Shipping

logger = logging.getLogger(__name__)


def create_shipment(order, *, agency_code=None, document_number=None):
    """Emite la OF del pedido en Starken y guarda su numero de seguimiento.

    No cambia el estado del pedido: emitir la OF no es despachar. El pedido
    pasa a "enviado" cuando el paquete se entrega a Starken, como hoy.
    """
    if order.paid_at is None:
        raise starken.StarkenError(f'el pedido {order.pk} no esta pagado')
    existing = Shipment.objects.filter(order=order).first()
    if existing:
        raise starken.StarkenError(
            f'el pedido {order.pk} ya tiene la OF {existing.tracking_number}')

    payload = starken.emission_payload(
        order, agency_code=agency_code, document_number=document_number)
    tracking = starken.create_freight_order(payload)
    with transaction.atomic():
        shipment = Shipment.objects.create(
            order=order, carrier=Shipping.Carrier.starken, tracking_number=tracking)
        order.deliveryNumber = tracking
        order.save(update_fields=['deliveryNumber'])
    return shipment


def _orders_to_track():
    """Pedidos enviados por Starken con numero de seguimiento y sin estado final."""
    return (Order.objects
            .filter(status=Order.OrderStatus.shipping,
                    shipping_id__carrier=Shipping.Carrier.starken)
            .exclude(deliveryNumber__isnull=True).exclude(deliveryNumber='')
            .exclude(shipment__is_final=True)
            .select_related('shipment'))


def sync_tracking(now=None):
    """Actualiza el estado de los envios en curso. Devuelve (ok, con_error)."""
    now = now or timezone.now()
    ok = failed = 0
    for order in _orders_to_track():
        number = order.deliveryNumber.strip()
        shipment = getattr(order, 'shipment', None)
        if shipment is None:
            # El numero lo cargo la app admin a mano: se empieza a seguir igual.
            shipment = Shipment.objects.create(
                order=order, carrier=Shipping.Carrier.starken, tracking_number=number)
        elif shipment.tracking_number != number:
            shipment.tracking_number = number
        if not number.isdigit():
            shipment.last_error = f'numero de seguimiento no numerico: {number!r}'
            shipment.save()
            failed += 1
            continue
        try:
            status, final = starken.tracking_status(number)
        except starken.StarkenError as exc:
            shipment.last_error = str(exc)
            shipment.save()
            failed += 1
            logger.warning('Seguimiento Starken de la OF %s: %s', number, exc)
            continue
        if status != shipment.status:
            shipment.status = status
            shipment.status_at = now
        shipment.is_final = final
        shipment.last_error = ''
        shipment.save()
        ok += 1
    return ok, failed

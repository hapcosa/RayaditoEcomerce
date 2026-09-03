import os

import mercadopago
from django.db import transaction
from django.db.models import Sum
from django.utils.text import slugify

from carrito.models import Carrito, CarritoItem
from orders.models import Order, OrderItem
from .models import Payments


PAYMENT_TO_ORDER_STATUS = {
    Payments.PaymentStatus.APPROVED.value: Order.OrderStatus.processed,
    Payments.PaymentStatus.REJECTED.value: Order.OrderStatus.refused,
    Payments.PaymentStatus.CANCELLED.value: Order.OrderStatus.cancelled,
    Payments.PaymentStatus.REFUNDED.value: Order.OrderStatus.cancelled,
    Payments.PaymentStatus.CHARGED_BACK.value: Order.OrderStatus.cancelled,
}


class MercadoPagoConfigurationError(Exception):
    pass


class UnknownOrderError(Exception):
    """La notificacion no se puede asociar a ninguna orden local.

    Reintentar no cambia nada: el webhook debe acusar recibo igual, si no
    MercadoPago reintenta en bucle y termina deshabilitando el endpoint.
    """


def mercadopago_token():
    return os.environ.get('MERCADOPAGO_ACCESS_TOKEN') or os.environ.get('TOKENMERCADOPAGOTEST')


def mercadopago_sdk():
    token = mercadopago_token()
    if not token:
        raise MercadoPagoConfigurationError('MercadoPago no está configurado')
    return mercadopago.SDK(token)


def sync_cart_total(cart):
    total = CarritoItem.objects.filter(carrito=cart).aggregate(total=Sum('count'))['total'] or 0
    Carrito.objects.filter(id=cart.id).update(total_items=total)


def has_stock(product, count):
    variant_stock = product.variants.filter(is_active=True).aggregate(total=Sum('stock'))['total']
    if variant_stock is None:
        return not product.sold
    return variant_stock >= count


def deduct_product_stock(product, count):
    variants = product.variants.filter(is_active=True).order_by('id')
    if not variants.exists():
        product.sold = True
        product.save(update_fields=['sold'])
        return

    remaining = count
    for variant in variants:
        if remaining <= 0:
            break
        quantity = min(variant.stock, remaining)
        variant.stock -= quantity
        variant.save(update_fields=['stock'])
        remaining -= quantity


def create_order_item(order, product, count):
    OrderItem.objects.create(
        product=product,
        order=order,
        name=product.name,
        price=int(product.price),
        count=count,
    )


def payment_status(raw_status):
    value = slugify(raw_status or '').replace('-', '_')
    valid_statuses = {choice.value for choice in Payments.PaymentStatus}
    if value in valid_statuses:
        return value
    return Payments.PaymentStatus.UNKNOWN.value


def apply_approved_payment(payment):
    if payment.stock_deducted:
        return

    for item in OrderItem.objects.select_related('product').filter(order=payment.order):
        deduct_product_stock(item.product, item.count)

    if payment.order.user_id:
        cart = Carrito.objects.filter(user=payment.order.user).first()
        if cart:
            product_ids = OrderItem.objects.filter(order=payment.order).values_list('product_id', flat=True)
            CarritoItem.objects.filter(carrito=cart, product_id__in=product_ids).delete()
            sync_cart_total(cart)

    payment.stock_deducted = True
    payment.save(update_fields=['stock_deducted', 'updated_at'])


def record_payment(payment_data):
    external_reference = str(payment_data.get('external_reference') or '')
    if not external_reference.isdigit():
        raise UnknownOrderError(
            f'external_reference no utilizable: {external_reference!r}')
    if not payment_data.get('id'):
        raise UnknownOrderError('la notificacion no trae id de pago')

    order = Order.objects.filter(id=int(external_reference)).first()
    if order is None:
        raise UnknownOrderError(f'no existe la orden {external_reference}')
    status = payment_status(payment_data.get('status'))
    order_status = PAYMENT_TO_ORDER_STATUS.get(status, Order.OrderStatus.not_processed)

    with transaction.atomic():
        order.status = order_status
        order.transaction_id = str(payment_data['id'])
        order.save(update_fields=['status', 'transaction_id'])

        installments = int(payment_data.get('installments') or 1)
        payment, _created = Payments.objects.update_or_create(
            order=order,
            defaults={
                'payment_id': int(payment_data['id']),
                'status': status,
                'status_detail': payment_data.get('status_detail') or '',
                'external_reference': external_reference,
                'payment_method_id': payment_data.get('payment_method_id') or '',
                'typepayment': payment_data.get('payment_type_id') or '',
                'cuotas': installments > 1,
                'raw_response': payment_data,
            },
        )
        if status == Payments.PaymentStatus.APPROVED:
            apply_approved_payment(payment)
    return payment


def fetch_payment(payment_id):
    """Devuelve el pago remoto, o None si MercadoPago no lo reconoce.

    El SDK no levanta excepcion ante un 404: entrega el cuerpo del error en
    'response'. Ese dict es truthy, asi que sin mirar el status HTTP un id
    inexistente (los que manda el simulador del panel) se colaba hasta
    record_payment y reventaba.
    """
    payment_response = mercadopago_sdk().payment().get(payment_id)
    http_status = payment_response.get('status', 200)
    if http_status >= 400:
        return None
    payload = payment_response.get('response') or {}
    return payload if payload.get('id') else None


def sync_payment(payment_id):
    payment_data = fetch_payment(payment_id)
    if not payment_data:
        raise ValueError('respuesta de pago inválida')
    return record_payment(payment_data)

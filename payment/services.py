import os

import mercadopago
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
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
    order = get_object_or_404(Order, id=int(external_reference))
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
    payment_response = mercadopago_sdk().payment().get(payment_id)
    return payment_response.get('response', {})


def sync_payment(payment_id):
    payment_data = fetch_payment(payment_id)
    if not payment_data:
        raise ValueError('respuesta de pago inválida')
    return record_payment(payment_data)

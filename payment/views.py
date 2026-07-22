import hashlib
import hmac
import os

import mercadopago
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from carrito.models import Carrito, CarritoItem
from orders.models import Order, OrderItem
from product.models import Product
from shipping.models import Shipping
from user_profile.models import UserProfile
from .models import Payments


PAYMENT_TO_ORDER_STATUS = {
    Payments.PaymentStatus.APPROVED.value: Order.OrderStatus.processed,
    Payments.PaymentStatus.REJECTED.value: Order.OrderStatus.refused,
    Payments.PaymentStatus.CANCELLED.value: Order.OrderStatus.cancelled,
    Payments.PaymentStatus.REFUNDED.value: Order.OrderStatus.cancelled,
    Payments.PaymentStatus.CHARGED_BACK.value: Order.OrderStatus.cancelled,
}


def _mercadopago_token():
    return os.environ.get('MERCADOPAGO_ACCESS_TOKEN') or os.environ.get('TOKENMERCADOPAGOTEST')


def _sdk():
    return mercadopago.SDK(_mercadopago_token())


def _frontend_url():
    return os.environ.get('FRONTEND_BASE_URL', 'http://127.0.0.1:5173')


def _notification_url(request):
    configured = os.environ.get('MERCADOPAGO_NOTIFICATION_URL')
    if configured:
        return configured
    return request.build_absolute_uri('/api/payment/webhook')


def _order_items_payload(order):
    return [
        {
            'id': str(item.product_id),
            'title': item.name,
            'currency_id': 'CLP',
            'description': item.product.description,
            'category_id': str(item.product.category_id),
            'quantity': item.count,
            'unit_price': int(item.price),
        }
        for item in OrderItem.objects.select_related('product').filter(order=order)
    ]


def _preference_data(request, order):
    base_url = _frontend_url()
    return {
        'items': _order_items_payload(order),
        'notification_url': _notification_url(request),
        'back_urls': {
            'success': f'{base_url}/success',
            'failure': f'{base_url}/checkout',
            'pending': f'{base_url}/checkout',
        },
        'auto_return': 'approved',
        'external_reference': str(order.id),
        'expires': True,
        'payer': {
            'name': (order.full_name or '').split(' ', 1)[0],
            'surname': (order.full_name or '').split(' ', 1)[1] if ' ' in (order.full_name or '') else '',
            'email': order.user.email if order.user_id else order.email,
            'phone': {'area_code': '+56', 'number': order.telephone_number},
            'address': {
                'street_name': order.address_line_1,
                'street_number': '',
                'zip_code': order.postal_zip_code,
            },
        },
    }


def _sync_cart_total(cart):
    total = CarritoItem.objects.filter(carrito=cart).aggregate(total=Sum('count'))['total'] or 0
    Carrito.objects.filter(id=cart.id).update(total_items=total)


def _has_stock(product, count):
    variant_stock = product.variants.filter(is_active=True).aggregate(total=Sum('stock'))['total']
    if variant_stock is None:
        return not product.sold
    return variant_stock >= count


def _deduct_product_stock(product, count):
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


def _create_order_item(order, product, count):
    OrderItem.objects.create(
        product=product,
        order=order,
        name=product.name,
        price=int(product.price),
        count=count,
    )


def _create_authenticated_order(request):
    profile = get_object_or_404(UserProfile, id=int(request.data['profile_id']), user=request.user)
    shipping = get_object_or_404(Shipping, id=int(request.data['shipping_id']))
    cart = get_object_or_404(Carrito, user=request.user)
    cart_items = CarritoItem.objects.select_related('product').filter(carrito=cart)
    if not cart_items.exists():
        return None, Response({'error': 'No tienes productos en tu carrito'},
                              status=status.HTTP_404_NOT_FOUND)

    for item in cart_items:
        if not _has_stock(item.product, item.count):
            return None, Response({'error': f'Stock insuficiente para {item.product.name}'},
                                  status=status.HTTP_409_CONFLICT)

    amount = sum(int(item.product.price) * item.count for item in cart_items)
    order = Order.objects.create(
        user=request.user,
        profile=profile,
        amount=amount,
        full_name=f'{profile.first_name} {profile.last_name}'.strip(),
        address_line_1=profile.address_line_1,
        city=profile.city,
        region=profile.country_region,
        postal_zip_code=profile.zipcode,
        telephone_number=profile.phone,
        shipping_id=shipping,
    )
    for item in cart_items:
        _create_order_item(order, item.product, item.count)
    return order, None


def _create_guest_order(request):
    shipping = get_object_or_404(Shipping, id=int(request.data['shipping_id']))
    items = request.data.get('items') or []
    if not items:
        return None, Response({'error': 'No tienes productos en tu carrito'},
                              status=status.HTTP_404_NOT_FOUND)

    normalized_items = []
    for entry in items:
        product_data = entry.get('product', entry)
        product = get_object_or_404(Product, id=int(product_data['id']))
        count = max(int(entry.get('count', product_data.get('count', 1))), 1)
        if not _has_stock(product, count):
            return None, Response({'error': f'Stock insuficiente para {product.name}'},
                                  status=status.HTTP_409_CONFLICT)
        normalized_items.append((product, count))

    amount = sum(int(product.price) * count for product, count in normalized_items)
    order = Order.objects.create(
        email=request.data.get('email', ''),
        amount=amount,
        full_name=f"{request.data.get('first_name', '')} {request.data.get('last_name', '')}".strip(),
        address_line_1=request.data.get('address_line_1', ''),
        city=request.data.get('city', ''),
        region=request.data.get('state_province_region', ''),
        postal_zip_code=request.data.get('postal_zip_code', ''),
        telephone_number=request.data.get('telephone_number', ''),
        shipping_id=shipping,
    )
    for product, count in normalized_items:
        _create_order_item(order, product, count)
    return order, None


def _create_preference(request, order):
    preference_response = _sdk().preference().create(_preference_data(request, order))
    return preference_response.get('response', preference_response)


def _extract_payment_id(request):
    return (
        request.query_params.get('data.id')
        or request.query_params.get('id')
        or (request.data.get('data') or {}).get('id')
        or request.data.get('id')
    )


def _signature_parts(x_signature):
    parts = {}
    for part in (x_signature or '').split(','):
        key, separator, value = part.partition('=')
        if separator:
            parts[key.strip()] = value.strip()
    return parts


def _valid_webhook_signature(request, data_id):
    secret = os.environ.get('MERCADOPAGO_WEBHOOK_SECRET', '')
    if not secret:
        return True

    x_signature = request.headers.get('x-signature', '')
    x_request_id = request.headers.get('x-request-id', '')
    parts = _signature_parts(x_signature)
    timestamp = parts.get('ts')
    received_signature = parts.get('v1')
    if not timestamp or not received_signature or not x_request_id or not data_id:
        return False

    manifest = f'id:{str(data_id).lower()};request-id:{x_request_id};ts:{timestamp};'
    expected_signature = hmac.new(
        secret.encode(),
        msg=manifest.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, received_signature)


def _payment_status(raw_status):
    value = slugify(raw_status or '').replace('-', '_')
    valid_statuses = {choice.value for choice in Payments.PaymentStatus}
    if value in valid_statuses:
        return value
    return Payments.PaymentStatus.UNKNOWN


def _apply_approved_payment(payment):
    if payment.stock_deducted:
        return

    for item in OrderItem.objects.select_related('product').filter(order=payment.order):
        _deduct_product_stock(item.product, item.count)

    if payment.order.user_id:
        cart = Carrito.objects.filter(user=payment.order.user).first()
        if cart:
            product_ids = OrderItem.objects.filter(order=payment.order).values_list('product_id', flat=True)
            CarritoItem.objects.filter(carrito=cart, product_id__in=product_ids).delete()
            _sync_cart_total(cart)

    payment.stock_deducted = True
    payment.save(update_fields=['stock_deducted', 'updated_at'])


def _record_payment(payment_data):
    external_reference = str(payment_data.get('external_reference') or '')
    order = get_object_or_404(Order, id=int(external_reference))
    payment_status = _payment_status(payment_data.get('status'))
    order_status = PAYMENT_TO_ORDER_STATUS.get(payment_status, Order.OrderStatus.not_processed)

    with transaction.atomic():
        order.status = order_status
        order.transaction_id = str(payment_data['id'])
        order.save(update_fields=['status', 'transaction_id'])

        installments = int(payment_data.get('installments') or 1)
        payment, _created = Payments.objects.update_or_create(
            order=order,
            defaults={
                'payment_id': int(payment_data['id']),
                'status': payment_status,
                'status_detail': payment_data.get('status_detail') or '',
                'external_reference': external_reference,
                'payment_method_id': payment_data.get('payment_method_id') or '',
                'typepayment': payment_data.get('payment_type_id') or '',
                'cuotas': installments > 1,
                'raw_response': payment_data,
            },
        )
        if payment_status == Payments.PaymentStatus.APPROVED:
            _apply_approved_payment(payment)
    return order


class ProcessPaymentView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        if not _mercadopago_token():
            return Response({'error': 'MercadoPago no está configurado'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            if 'orderId' in request.data:
                order = get_object_or_404(Order, id=int(request.data['orderId']))
                if order.user_id and (not request.user.is_authenticated or order.user_id != request.user.id):
                    return Response({'error': 'No tienes permiso para pagar esta orden'},
                                    status=status.HTTP_403_FORBIDDEN)
            elif request.user.is_authenticated:
                order, error = _create_authenticated_order(request)
                if error:
                    return error
            else:
                order, error = _create_guest_order(request)
                if error:
                    return error
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Datos de pago inválidos'},
                            status=status.HTTP_400_BAD_REQUEST)

        preference = _create_preference(request, order)
        return Response({'response': preference, 'order_id': order.id},
                        status=status.HTTP_200_OK)


class MercadoPagoResponse(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        payment_id = _extract_payment_id(request)
        if not payment_id:
            return Response({'error': 'payment id requerido'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not _valid_webhook_signature(request, payment_id):
            return Response({'error': 'firma inválida'},
                            status=status.HTTP_401_UNAUTHORIZED)
        if not _mercadopago_token():
            return Response({'error': 'MercadoPago no está configurado'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment_response = _sdk().payment().get(payment_id)
        payment_data = payment_response.get('response', {})
        if not payment_data:
            return Response({'error': 'respuesta de pago inválida'},
                            status=status.HTTP_502_BAD_GATEWAY)

        _record_payment(payment_data)
        return Response({'status': 'finish'}, status=status.HTTP_200_OK)


class StatusPaymentView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        order_id = request.query_params.get('order_id')
        payment_id = request.query_params.get('payment_id')
        if order_id:
            order = get_object_or_404(Order, id=int(order_id))
            payment = Payments.objects.filter(order=order).first()
        elif payment_id:
            payment = get_object_or_404(Payments, payment_id=int(payment_id))
            order = payment.order
        else:
            return Response({'error': 'order_id o payment_id requerido'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'order_id': order.id,
            'order_status': order.status,
            'payment_status': payment.status if payment else None,
            'transaction_id': order.transaction_id,
        }, status=status.HTTP_200_OK)

import hashlib
import hmac
import os

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from carrito.models import Carrito, CarritoItem
from orders.models import Order, OrderItem
from product.models import Product
from shipping.models import Shipping
from user_profile.models import UserProfile
from .models import Payments
from . import services


def _frontend_url():
    return os.environ.get('FRONTEND_BASE_URL', 'http://127.0.0.1:5173')


def _notification_url(request):
    configured = os.environ.get('MERCADOPAGO_NOTIFICATION_URL')
    if configured:
        return configured
    return request.build_absolute_uri('/api/payment/webhook')


def _order_items_payload(order):
    items = [
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
    if order.shipping_price:
        shipping_name = order.shipping_id.name if order.shipping_id else 'Envio'
        items.append({
            'id': f'shipping-{order.shipping_id_id or order.id}',
            'title': f'Envio - {shipping_name}',
            'currency_id': 'CLP',
            'description': 'Costo de envio',
            'category_id': 'shipping',
            'quantity': 1,
            'unit_price': int(order.shipping_price),
        })
    return items


def _shipping_price(shipping):
    return int(shipping.price or 0)


def _preference_data(request, order):
    base_url = _frontend_url()
    return {
        'items': _order_items_payload(order),
        'notification_url': _notification_url(request),
        'back_urls': {
            'success': f'{base_url}/success',
            'failure': f'{base_url}/success',
            'pending': f'{base_url}/success',
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


def _create_authenticated_order(request):
    profile = get_object_or_404(UserProfile, id=int(request.data['profile_id']), user=request.user)
    shipping = get_object_or_404(Shipping, id=int(request.data['shipping_id']))
    cart = get_object_or_404(Carrito, user=request.user)
    cart_items = CarritoItem.objects.select_related('product').filter(carrito=cart)
    if not cart_items.exists():
        return None, Response({'error': 'No tienes productos en tu carrito'},
                              status=status.HTTP_404_NOT_FOUND)

    for item in cart_items:
        if not services.has_stock(item.product, item.count):
            return None, Response({'error': f'Stock insuficiente para {item.product.name}'},
                                  status=status.HTTP_409_CONFLICT)

    shipping_price = _shipping_price(shipping)
    amount = sum(int(item.product.price) * item.count for item in cart_items) + shipping_price
    order = Order.objects.create(
        user=request.user,
        profile=profile,
        amount=amount,
        shipping_price=shipping_price,
        full_name=f'{profile.first_name} {profile.last_name}'.strip(),
        address_line_1=profile.address_line_1,
        city=profile.city,
        region=profile.country_region,
        postal_zip_code=profile.zipcode,
        telephone_number=profile.phone,
        shipping_id=shipping,
    )
    for item in cart_items:
        services.create_order_item(order, item.product, item.count)
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
        if not services.has_stock(product, count):
            return None, Response({'error': f'Stock insuficiente para {product.name}'},
                                  status=status.HTTP_409_CONFLICT)
        normalized_items.append((product, count))

    shipping_price = _shipping_price(shipping)
    amount = sum(int(product.price) * count for product, count in normalized_items) + shipping_price
    order = Order.objects.create(
        email=request.data.get('email', ''),
        amount=amount,
        shipping_price=shipping_price,
        full_name=f"{request.data.get('first_name', '')} {request.data.get('last_name', '')}".strip(),
        address_line_1=request.data.get('address_line_1', ''),
        city=request.data.get('city', ''),
        region=request.data.get('state_province_region', ''),
        postal_zip_code=request.data.get('postal_zip_code', ''),
        telephone_number=request.data.get('telephone_number', ''),
        shipping_id=shipping,
    )
    for product, count in normalized_items:
        services.create_order_item(order, product, count)
    return order, None


def _create_preference(request, order):
    preference_response = services.mercadopago_sdk().preference().create(_preference_data(request, order))
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


class ProcessPaymentView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        if not services.mercadopago_token():
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
        if not services.mercadopago_token():
            return Response({'error': 'MercadoPago no está configurado'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment_data = services.fetch_payment(payment_id)
        if not payment_data:
            return Response({'error': 'respuesta de pago inválida'},
                            status=status.HTTP_502_BAD_GATEWAY)

        services.record_payment(payment_data)
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

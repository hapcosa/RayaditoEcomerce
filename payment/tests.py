import os
import hmac
import hashlib
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from carrito.models import Carrito, CarritoItem
from category.models import Category
from orders.models import Order, OrderItem
from payment.models import Payments
from product.models import Product, ProductVariant
from shipping.models import Shipping
from user_profile.models import UserProfile

User = get_user_model()


class FakePreferenceClient:
    def __init__(self, response):
        self.response = response
        self.created_payload = None

    def create(self, payload):
        self.created_payload = payload
        return {'response': self.response}


class FakePaymentClient:
    def __init__(self, response):
        self.response = response
        self.requested_payment_id = None

    def get(self, payment_id):
        self.requested_payment_id = str(payment_id)
        return {'response': self.response}


class FakeMercadoPagoSDK:
    def __init__(self, preference_response=None, payment_response=None):
        self.preference_client = FakePreferenceClient(preference_response or {})
        self.payment_client = FakePaymentClient(payment_response or {})

    def preference(self):
        return self.preference_client

    def payment(self):
        return self.payment_client


class MercadoPagoFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@rayadito.cl',
            password='Testpass123',
            first_name='Ana',
            last_name='Ríos',
        )
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de plata',
            product_type='joya',
            description='Hecho a mano',
            price=25000,
            compare_price=0,
            category=self.category,
            photo='',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='ANI-1',
            stock=5,
        )
        self.shipping = Shipping.objects.create(
            name='Retiro',
            time_to_delivery='1 día',
            description='Retiro en taller',
            photo='',
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            first_name='Ana',
            last_name='Ríos',
            address_line_1='Calle 1',
            city='Ancud',
            zipcode='5700000',
            phone='912345678',
            country_region='RM',
        )
        self.cart = Carrito.objects.get(user=self.user)

    @mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
    def test_make_payment_creates_preference_with_cart_counts(self):
        CarritoItem.objects.create(carrito=self.cart, product=self.product, count=2)
        fake_sdk = FakeMercadoPagoSDK(
            preference_response={'id': 'pref_123', 'init_point': 'https://mp.test/pref_123'},
        )
        self.client.force_authenticate(self.user)

        with mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            res = self.client.post('/api/payment/make-payment', {
                'shipping_id': self.shipping.id,
                'profile_id': self.profile.id,
            }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        order = Order.objects.get(id=res.data['order_id'])
        item = OrderItem.objects.get(order=order)
        self.assertEqual(order.amount, 50000)
        self.assertEqual(item.price, 25000)
        self.assertEqual(item.count, 2)
        self.assertEqual(fake_sdk.preference_client.created_payload['external_reference'], str(order.id))
        self.assertEqual(fake_sdk.preference_client.created_payload['items'][0]['quantity'], 2)
        self.assertEqual(fake_sdk.preference_client.created_payload['items'][0]['unit_price'], 25000)
        self.assertEqual(
            fake_sdk.preference_client.created_payload['back_urls'],
            {
                'success': 'http://127.0.0.1:5173/success',
                'failure': 'http://127.0.0.1:5173/success',
                'pending': 'http://127.0.0.1:5173/success',
            },
        )

    @mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
    def test_approved_webhook_is_idempotent_and_deducts_stock_once(self):
        order = Order.objects.create(
            user=self.user,
            amount=50000,
            shipping_id=self.shipping,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            price=25000,
            count=2,
        )
        CarritoItem.objects.create(carrito=self.cart, product=self.product, count=2)
        self.cart.total_items = 2
        self.cart.save(update_fields=['total_items'])
        payment_response = {
            'id': 123456,
            'external_reference': str(order.id),
            'status': 'approved',
            'status_detail': 'accredited',
            'payment_method_id': 'visa',
            'payment_type_id': 'credit_card',
            'installments': 3,
        }
        fake_sdk = FakeMercadoPagoSDK(payment_response=payment_response)

        with mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            first = self.client.post('/api/payment/webhook', {
                'type': 'payment',
                'data': {'id': '123456'},
            }, format='json')
            second = self.client.post('/api/payment/webhook', {
                'type': 'payment',
                'data': {'id': '123456'},
            }, format='json')

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.variant.refresh_from_db()
        payment = Payments.objects.get(order=order)
        self.assertEqual(order.status, Order.OrderStatus.processed)
        self.assertEqual(order.transaction_id, '123456')
        self.assertEqual(payment.status, Payments.PaymentStatus.APPROVED)
        self.assertTrue(payment.cuotas)
        self.assertTrue(payment.stock_deducted)
        self.assertEqual(self.variant.stock, 3)
        self.assertFalse(CarritoItem.objects.filter(carrito=self.cart).exists())
        self.assertEqual(Carrito.objects.get(id=self.cart.id).total_items, 0)

    @mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
    def test_rejected_webhook_marks_order_refused_without_deducting_stock(self):
        order = Order.objects.create(amount=25000, shipping_id=self.shipping)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            price=25000,
            count=1,
        )
        payment_response = {
            'id': 222,
            'external_reference': str(order.id),
            'status': 'rejected',
            'status_detail': 'cc_rejected_other_reason',
            'installments': 1,
        }
        fake_sdk = FakeMercadoPagoSDK(payment_response=payment_response)

        with mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            res = self.client.post('/api/payment/webhook', {
                'type': 'payment',
                'data': {'id': '222'},
            }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.variant.refresh_from_db()
        payment = Payments.objects.get(order=order)
        self.assertEqual(order.status, Order.OrderStatus.refused)
        self.assertEqual(payment.status, Payments.PaymentStatus.REJECTED)
        self.assertFalse(payment.stock_deducted)
        self.assertEqual(self.variant.stock, 5)

    @mock.patch.dict(os.environ, {
        'MERCADOPAGO_ACCESS_TOKEN': 'test-token',
        'MERCADOPAGO_WEBHOOK_SECRET': 'secret',
    }, clear=False)
    def test_webhook_rejects_invalid_signature(self):
        fake_sdk = FakeMercadoPagoSDK(payment_response={})
        bad_signature = hmac.new(
            b'wrong-secret',
            msg=b'id:123;request-id:req-1;ts:1700000000;',
            digestmod=hashlib.sha256,
        ).hexdigest()

        with mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            res = self.client.post(
                '/api/payment/webhook',
                {'type': 'payment', 'data': {'id': '123'}},
                format='json',
                HTTP_X_SIGNATURE=f'ts=1700000000,v1={bad_signature}',
                HTTP_X_REQUEST_ID='req-1',
            )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsNone(fake_sdk.payment_client.requested_payment_id)

    @mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
    def test_reconcile_command_syncs_payment_by_id(self):
        order = Order.objects.create(
            user=self.user,
            amount=50000,
            shipping_id=self.shipping,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            price=25000,
            count=2,
        )
        CarritoItem.objects.create(carrito=self.cart, product=self.product, count=2)
        self.cart.total_items = 2
        self.cart.save(update_fields=['total_items'])
        Payments.objects.create(
            order=order,
            payment_id=333,
            status=Payments.PaymentStatus.PENDING,
            external_reference=str(order.id),
        )
        payment_response = {
            'id': 333,
            'external_reference': str(order.id),
            'status': 'approved',
            'status_detail': 'accredited',
            'payment_method_id': 'visa',
            'payment_type_id': 'credit_card',
            'installments': 1,
        }
        fake_sdk = FakeMercadoPagoSDK(payment_response=payment_response)
        output = StringIO()

        with mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            call_command('reconcile_mercadopago_payments', '--payment-id', '333', stdout=output)

        order.refresh_from_db()
        self.variant.refresh_from_db()
        payment = Payments.objects.get(order=order)
        self.assertEqual(fake_sdk.payment_client.requested_payment_id, '333')
        self.assertEqual(order.status, Order.OrderStatus.processed)
        self.assertEqual(payment.status, Payments.PaymentStatus.APPROVED)
        self.assertTrue(payment.stock_deducted)
        self.assertEqual(self.variant.stock, 3)
        self.assertFalse(CarritoItem.objects.filter(carrito=self.cart).exists())
        self.assertIn('Reconciled 1 MercadoPago payment(s).', output.getvalue())

    @mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
    def test_reconcile_command_without_ids_syncs_pending_payments(self):
        order = Order.objects.create(amount=25000, shipping_id=self.shipping)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            name=self.product.name,
            price=25000,
            count=1,
        )
        Payments.objects.create(
            order=order,
            payment_id=444,
            status=Payments.PaymentStatus.PENDING,
            external_reference=str(order.id),
        )
        payment_response = {
            'id': 444,
            'external_reference': str(order.id),
            'status': 'rejected',
            'status_detail': 'cc_rejected_other_reason',
            'installments': 1,
        }
        fake_sdk = FakeMercadoPagoSDK(payment_response=payment_response)

        with mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            call_command('reconcile_mercadopago_payments')

        order.refresh_from_db()
        payment = Payments.objects.get(order=order)
        self.assertEqual(fake_sdk.payment_client.requested_payment_id, '444')
        self.assertEqual(order.status, Order.OrderStatus.refused)
        self.assertEqual(payment.status, Payments.PaymentStatus.REJECTED)
        self.assertFalse(payment.stock_deducted)

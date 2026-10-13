"""Derecho a retracto: formulario publico y confirmacion escrita de la compra."""
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from category.models import Category
from notifications.services import notify_customer_paid_order
from orders.models import Order, OrderItem, WithdrawalRequest
from product.models import Product
from shipping.models import Shipping

User = get_user_model()

SETTINGS = override_settings(
    ADMIN_NOTIFY_EMAILS=['duena@rayadito.cl'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_BASE_URL='https://piedrasdelrayadito.cl',
    BACKEND_BASE_URL='https://piedrasdelrayadito.cl',
)


@SETTINGS
class WithdrawalBase(APITestCase):
    url = '/api/orders/withdrawal'

    def setUp(self):
        cache.clear()  # el throttle cuenta en cache entre tests
        category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de ágata', product_type='joya', description='x',
            price=25000, compare_price=0, category=category, photo='',
        )
        shipping = Shipping.objects.create(
            name='Starken', time_to_delivery='3 días', description='x',
            price=4500, photo='',
        )
        self.order = Order.objects.create(
            email='ana@cliente.cl', amount=29500, shipping_price=4500,
            full_name='Ana Ríos', address_line_1='Calle 1', city='Ancud',
            telephone_number='912345678', shipping_id=shipping,
            transaction_id='130551234567', paid_at=timezone.now(),
            status=Order.OrderStatus.processed,
        )
        OrderItem.objects.create(order=self.order, product=self.product,
                                 name=self.product.name, price=25000, count=1)
        push = mock.patch('orders.withdrawal.push_admins', return_value=0)
        self.push = push.start()
        self.addCleanup(push.stop)

    def request(self, number=None, email='ana@cliente.cl', reason=''):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.url, {
                'order_number': number or self.order.transaction_id,
                'email': email, 'reason': reason,
            }, format='json')


class WithdrawalRequestTests(WithdrawalBase):
    def test_creates_request_with_code_and_notifies_both_sides(self):
        response = self.request(reason='No era la talla')
        self.assertEqual(response.status_code, 201, response.data)
        withdrawal = WithdrawalRequest.objects.get()
        self.assertEqual(response.data['code'], withdrawal.code)
        self.assertTrue(withdrawal.code.startswith(f'RET-{self.order.id}-'))
        self.assertEqual(withdrawal.reason, 'No era la talla')
        self.assertEqual(withdrawal.status, WithdrawalRequest.Status.RECEIVED)

        to_customer = [m for m in mail.outbox if m.to == ['ana@cliente.cl']]
        to_owner = [m for m in mail.outbox if m.to == ['duena@rayadito.cl']]
        self.assertEqual(len(to_customer), 1)
        self.assertIn(withdrawal.code, to_customer[0].body)
        self.assertIn('#130551234567', to_customer[0].body)
        self.assertEqual(to_customer[0].reply_to, ['duena@rayadito.cl'])
        self.assertEqual(len(to_owner), 1)
        self.assertIn('No era la talla', to_owner[0].body)
        self.push.assert_called_once()

    def test_accepts_internal_id_hash_and_email_case(self):
        response = self.request(number=f'#{self.order.id}', email='ANA@Cliente.cl')
        self.assertEqual(response.status_code, 201, response.data)

    def test_reason_is_optional(self):
        self.assertEqual(self.request().status_code, 201)

    def test_wrong_email_looks_like_missing_order(self):
        wrong = self.request(email='otra@persona.cl')
        missing = self.request(number='999999999')
        self.assertEqual(wrong.status_code, 404)
        self.assertEqual(wrong.data, missing.data)
        self.assertFalse(WithdrawalRequest.objects.exists())

    def test_unpaid_order_is_not_found(self):
        Order.objects.filter(pk=self.order.pk).update(paid_at=None)
        self.assertEqual(self.request().status_code, 404)

    def test_registered_user_email_matches(self):
        user = User.objects.create_user(email='cuenta@cliente.cl', password='x',
                                        first_name='A', last_name='R')
        Order.objects.filter(pk=self.order.pk).update(user=user, email=None)
        self.assertEqual(self.request(email='cuenta@cliente.cl').status_code, 201)

    def test_repeated_request_returns_same_code(self):
        first = self.request()
        second = self.request()
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['already_requested'])
        self.assertEqual(first.data['code'], second.data['code'])
        self.assertEqual(WithdrawalRequest.objects.count(), 1)

    def test_closed_request_allows_a_new_one(self):
        self.request()
        WithdrawalRequest.objects.update(status=WithdrawalRequest.Status.REJECTED)
        self.assertEqual(self.request().status_code, 201)
        self.assertEqual(WithdrawalRequest.objects.count(), 2)

    def test_stale_jwt_does_not_block_the_form(self):
        self.client.credentials(HTTP_AUTHORIZATION='JWT token-vencido')
        self.assertEqual(self.request().status_code, 201)

    def test_is_throttled(self):
        statuses = [self.request(number='1').status_code for _ in range(6)]
        self.assertEqual(statuses[-1], 429)


@SETTINGS
class CustomerConfirmationTests(WithdrawalBase):
    def test_confirmation_mentions_withdrawal_right_and_link(self):
        self.assertTrue(notify_customer_paid_order(self.order))
        message = mail.outbox[0]
        self.assertEqual(message.to, ['ana@cliente.cl'])
        self.assertIn('#130551234567', message.subject)
        self.assertIn('1 x Anillo de ágata', message.body)
        self.assertIn('$29.500', message.body)
        self.assertIn('Derecho a retracto', message.body)
        self.assertIn('10 días', message.body)
        self.assertIn('https://piedrasdelrayadito.cl/arrepentimiento', message.body)

    @override_settings(FRONTEND_BASE_URL='')
    def test_without_domain_explains_how_to_withdraw_by_email(self):
        notify_customer_paid_order(self.order)
        self.assertIn('responde este correo', mail.outbox[0].body)

    def test_without_email_nothing_is_sent(self):
        Order.objects.filter(pk=self.order.pk).update(email=None)
        self.order.refresh_from_db()
        self.assertFalse(notify_customer_paid_order(self.order))
        self.assertEqual(len(mail.outbox), 0)

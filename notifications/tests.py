"""Aviso al admin cuando entra una venta."""
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import transaction
from django.test import override_settings
from rest_framework.test import APITestCase

from category.models import Category
from notifications.formatting import clp
from notifications.services import notify_paid_order_on_commit
from orders.models import Order, OrderItem
from payment import services
from payment.models import Payments
from product.models import Product
from shipping.models import Shipping

User = get_user_model()

NOTIFY = override_settings(
    ADMIN_NOTIFY_EMAILS=['duena@rayadito.cl'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    BACKEND_BASE_URL='https://api.piedrasdelrayadito.cl',
)


class ClpFormatTests(APITestCase):
    def test_thousands_use_dots(self):
        self.assertEqual(clp(29500), '29.500')
        self.assertEqual(clp(1250000), '1.250.000')
        self.assertEqual(clp(0), '0')
        self.assertEqual(clp(None), '0')


@NOTIFY
class AdminSaleEmailTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de plata', product_type='joya', description='Hecho a mano',
            price=25000, compare_price=0, category=self.category, photo='',
        )
        self.shipping = Shipping.objects.create(
            name='Starken', time_to_delivery='3 días', description='A sucursal',
            price=4500, photo='',
        )
        self.order = Order.objects.create(
            email='ana@cliente.cl', amount=54500, shipping_price=4500,
            full_name='Ana Ríos', address_line_1='Calle 1', city='Ancud',
            telephone_number='912345678', shipping_id=self.shipping,
        )
        OrderItem.objects.create(
            order=self.order, product=self.product, name=self.product.name,
            price=25000, count=2,
        )

    def _approve(self, payment_id=4242, status_value='approved'):
        """Corre `record_payment` dejando que los `on_commit` se ejecuten."""
        with self.captureOnCommitCallbacks(execute=True):
            return services.record_payment({
                'id': payment_id,
                'external_reference': str(self.order.id),
                'status': status_value,
                'status_detail': 'accredited',
                'installments': 1,
            })

    def test_an_approved_payment_emails_the_owner(self):
        self._approve()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['duena@rayadito.cl'])
        self.assertIn(f'#{self.order.id}', message.subject)
        self.assertIn('54.500', message.body)
        self.assertIn('Ana Ríos', message.body)
        self.assertIn('ana@cliente.cl', message.body)
        self.assertIn('2 x Anillo de plata', message.body)
        self.assertIn('Starken', message.body)
        self.assertIn(
            f'https://api.piedrasdelrayadito.cl/admin/orders/order/{self.order.id}/change/',
            message.body,
        )

    def test_a_repeated_notification_does_not_email_twice(self):
        self._approve()
        self._approve()

        self.assertEqual(len(mail.outbox), 1)

    def test_a_rejected_payment_does_not_email(self):
        self._approve(status_value='rejected')

        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ADMIN_NOTIFY_EMAILS=[])
    def test_without_recipients_nothing_is_sent(self):
        self._approve()

        self.assertEqual(len(mail.outbox), 0)

    def test_the_email_waits_for_the_transaction_to_commit(self):
        # `record_payment` corre dentro de `transaction.atomic()`. Si algo
        # revienta ahi la venta no queda guardada, y un correo ya enviado no se
        # puede des-enviar: por eso el aviso va en `on_commit`.
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    notify_paid_order_on_commit(self.order)
                    raise RuntimeError('boom')

        self.assertEqual(len(mail.outbox), 0)

    def test_an_smtp_failure_does_not_break_the_sale(self):
        with mock.patch('notifications.services.EmailMessage.send',
                        side_effect=OSError('smtp caido')):
            payment = self._approve()

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.processed)
        self.assertEqual(payment.status, Payments.PaymentStatus.APPROVED)
        self.assertTrue(payment.stock_deducted)
        self.assertTrue(Product.objects.get(id=self.product.id).sold)

    @override_settings(BACKEND_BASE_URL='')
    def test_without_a_domain_the_email_goes_without_a_link(self):
        self._approve()

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('/admin/orders/order/', mail.outbox[0].body)

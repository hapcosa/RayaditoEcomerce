"""Aviso al admin cuando entra una venta."""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core import mail
from django.db import transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from category.models import Category
from notifications import services as notify
from notifications.formatting import clp
from notifications.models import DevicePushToken
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


@override_settings(ADMIN_NOTIFY_EMAILS=[], EXPO_ACCESS_TOKEN='')
class PushTokenRegistrationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='duena@rayadito.cl', password='Testpass123',
            first_name='Duena', last_name='Rayadito',
        )
        self.customer = User.objects.create_user(
            email='ana@cliente.cl', password='Testpass123',
            first_name='Ana', last_name='Rios',
        )
        self.url = '/api/admin/push-tokens/'

    def test_registering_requires_staff(self):
        self.client.force_authenticate(self.customer)
        res = self.client.post(self.url, {'token': 'ExponentPushToken[abc]'},
                               format='json')

        self.assertEqual(res.status_code, 403)
        self.assertFalse(DevicePushToken.objects.exists())

    def test_staff_registers_a_device(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            self.url, {'token': 'ExponentPushToken[abc]', 'platform': 'android'},
            format='json',
        )

        self.assertEqual(res.status_code, 201, res.data)
        device = DevicePushToken.objects.get()
        self.assertEqual(device.user, self.admin)
        self.assertEqual(device.platform, 'android')
        self.assertTrue(device.is_active)

    def test_registering_twice_keeps_one_row_and_revives_it(self):
        DevicePushToken.objects.create(
            token='ExponentPushToken[abc]', user=self.admin,
            is_active=False, last_error='DeviceNotRegistered',
        )
        self.client.force_authenticate(self.admin)

        res = self.client.post(self.url, {'token': 'ExponentPushToken[abc]'},
                               format='json')

        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(DevicePushToken.objects.count(), 1)
        device = DevicePushToken.objects.get()
        self.assertTrue(device.is_active)
        self.assertEqual(device.last_error, '')

    def test_unregistering_deactivates_without_deleting(self):
        DevicePushToken.objects.create(token='ExponentPushToken[abc]',
                                       user=self.admin)
        self.client.force_authenticate(self.admin)

        res = self.client.delete(self.url, {'token': 'ExponentPushToken[abc]'},
                                 format='json')

        self.assertEqual(res.status_code, 204)
        device = DevicePushToken.objects.get()
        self.assertFalse(device.is_active)


@override_settings(ADMIN_NOTIFY_EMAILS=[], EXPO_ACCESS_TOKEN='')
class PushSendingTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='duena@rayadito.cl', password='Testpass123',
            first_name='Duena', last_name='Rayadito',
        )
        self.device = DevicePushToken.objects.create(
            token='ExponentPushToken[abc]', user=self.admin, platform='android',
        )

    def _expo_response(self, tickets):
        response = mock.Mock()
        response.json.return_value = {'data': tickets}
        response.raise_for_status.return_value = None
        return response

    def test_a_push_reaches_every_active_staff_device(self):
        DevicePushToken.objects.create(token='ExponentPushToken[tablet]',
                                       user=self.admin)
        with mock.patch('notifications.expo.requests.post',
                        return_value=self._expo_response(
                            [{'status': 'ok'}, {'status': 'ok'}])) as post:
            delivered = notify.push_admins('Hola', 'Cuerpo', {'order_id': 1})

        self.assertEqual(delivered, 2)
        messages = post.call_args.kwargs['json']
        self.assertEqual([m['to'] for m in messages],
                         ['ExponentPushToken[abc]', 'ExponentPushToken[tablet]'])
        self.assertEqual(messages[0]['data'], {'order_id': 1})

    def test_an_inactive_device_is_skipped(self):
        self.device.is_active = False
        self.device.save(update_fields=['is_active'])

        with mock.patch('notifications.expo.requests.post') as post:
            delivered = notify.push_admins('Hola', 'Cuerpo')

        self.assertEqual(delivered, 0)
        post.assert_not_called()

    def test_a_device_that_expo_rejects_is_deactivated(self):
        tickets = [{'status': 'error', 'message': 'no existe',
                    'details': {'error': 'DeviceNotRegistered'}}]
        with mock.patch('notifications.expo.requests.post',
                        return_value=self._expo_response(tickets)):
            delivered = notify.push_admins('Hola', 'Cuerpo')

        self.assertEqual(delivered, 0)
        self.device.refresh_from_db()
        self.assertFalse(self.device.is_active)
        self.assertEqual(self.device.last_error, 'DeviceNotRegistered')

    def test_another_expo_error_keeps_the_device_but_records_it(self):
        tickets = [{'status': 'error', 'message': 'mensaje muy largo',
                    'details': {'error': 'MessageTooBig'}}]
        with mock.patch('notifications.expo.requests.post',
                        return_value=self._expo_response(tickets)):
            notify.push_admins('Hola', 'Cuerpo')

        self.device.refresh_from_db()
        self.assertTrue(self.device.is_active)
        self.assertEqual(self.device.last_error, 'MessageTooBig')

    def test_expo_being_down_does_not_deactivate_anything(self):
        with mock.patch('notifications.expo.requests.post',
                        side_effect=OSError('sin red')):
            delivered = notify.push_admins('Hola', 'Cuerpo')

        self.assertEqual(delivered, 0)
        self.device.refresh_from_db()
        self.assertTrue(self.device.is_active)

    def test_the_access_token_travels_when_it_is_configured(self):
        with override_settings(EXPO_ACCESS_TOKEN='secreto'):
            with mock.patch('notifications.expo.requests.post',
                            return_value=self._expo_response(
                                [{'status': 'ok'}])) as post:
                notify.push_admins('Hola', 'Cuerpo')

        self.assertEqual(post.call_args.kwargs['headers']['authorization'],
                         'Bearer secreto')


@override_settings(
    ADMIN_NOTIFY_EMAILS=['duena@rayadito.cl'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EXPO_ACCESS_TOKEN='',
)
class PaidOrderPushTests(APITestCase):
    """El pago aprobado dispara los dos canales, y ninguno depende del otro."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='duena@rayadito.cl', password='Testpass123',
            first_name='Duena', last_name='Rayadito',
        )
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de plata', product_type='joya', description='Hecho a mano',
            price=25000, compare_price=0, category=self.category, photo='',
        )
        self.order = Order.objects.create(
            email='ana@cliente.cl', amount=54500, shipping_price=4500,
            full_name='Ana Ríos',
        )
        OrderItem.objects.create(
            order=self.order, product=self.product, name=self.product.name,
            price=25000, count=2,
        )
        self.device = DevicePushToken.objects.create(
            token='ExponentPushToken[abc]', user=self.admin, platform='android',
        )

    def _approve(self):
        with self.captureOnCommitCallbacks(execute=True):
            return services.record_payment({
                'id': 4242,
                'external_reference': str(self.order.id),
                'status': 'approved',
                'status_detail': 'accredited',
                'installments': 1,
            })

    def _ok_response(self):
        response = mock.Mock()
        response.json.return_value = {'data': [{'status': 'ok'}]}
        response.raise_for_status.return_value = None
        return response

    def test_an_approved_payment_pushes_the_sale(self):
        with mock.patch('notifications.expo.requests.post',
                        return_value=self._ok_response()) as post:
            self._approve()

        message = post.call_args.kwargs['json'][0]
        self.assertEqual(message['title'], 'Venta aprobada — $54.500')
        self.assertIn(f'Pedido #{self.order.id}', message['body'])
        self.assertIn('Ana Ríos', message['body'])
        self.assertIn('2 piezas', message['body'])
        self.assertEqual(message['data'],
                         {'type': 'paid_order', 'order_id': self.order.id})
        self.assertEqual(len(mail.outbox), 1)

    def test_a_push_failure_does_not_block_the_email(self):
        with mock.patch('notifications.expo.requests.post',
                        side_effect=OSError('sin red')):
            self._approve()

        self.assertEqual(len(mail.outbox), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.processed)

    def test_a_device_of_someone_who_is_no_longer_staff_gets_nothing(self):
        self.admin.is_staff = False
        self.admin.save(update_fields=['is_staff'])

        with mock.patch('notifications.expo.requests.post') as post:
            self._approve()

        post.assert_not_called()
        self.assertEqual(len(mail.outbox), 1)


@override_settings(
    ADMIN_NOTIFY_EMAILS=['duena@rayadito.cl'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    BACKEND_BASE_URL='https://api.piedrasdelrayadito.cl',
    DISPATCH_SLA_HOURS=72,
    DISPATCH_WARN_HOURS=24,
)
class PendingDispatchTests(APITestCase):
    """Aviso de plazo: con SLA 72 h y aviso 24 h antes, sale a las 48 h."""

    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de plata', product_type='joya', description='Hecho a mano',
            price=25000, compare_price=0, category=self.category, photo='',
        )
        self.now = timezone.now()

    def _order(self, hours_ago, status=Order.OrderStatus.processed, **extra):
        order = Order.objects.create(
            email='ana@cliente.cl', amount=29500, shipping_price=4500,
            full_name='Ana Ríos', status=status,
            paid_at=self.now - timedelta(hours=hours_ago), **extra,
        )
        OrderItem.objects.create(
            order=order, product=self.product, name=self.product.name,
            price=25000, count=1,
        )
        return order

    def _run(self, *args):
        out = StringIO()
        call_command('notify_pending_dispatch', *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_a_fresh_order_is_not_warned_about(self):
        self._order(hours_ago=10)

        self.assertEqual(list(notify.orders_to_warn(self.now)), [])
        self._run()
        self.assertEqual(len(mail.outbox), 0)

    def test_an_order_inside_the_warning_window_is_warned_about(self):
        order = self._order(hours_ago=50)

        self._run()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(f'#{order.id}', message.subject)
        self.assertIn('Plazo por vencer', message.subject)
        self.assertIn('quedan 22 horas', message.subject)
        self.assertIn('Ana Ríos', message.body)
        self.assertIn('Para despachar este pedido quedan 22 horas.', message.body)
        order.refresh_from_db()
        self.assertIsNotNone(order.dispatch_warned_at)

    def test_an_overdue_order_says_so(self):
        self._order(hours_ago=100)

        self._run()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Plazo vencido', mail.outbox[0].subject)
        self.assertIn('venció hace 28 horas', mail.outbox[0].subject)
        self.assertIn('El plazo para despachar este pedido venció hace 28 horas.',
                      mail.outbox[0].body)

    def test_an_order_is_only_warned_about_once(self):
        self._order(hours_ago=50)

        self._run()
        self._run()

        self.assertEqual(len(mail.outbox), 1)

    def test_a_dispatched_order_is_left_alone(self):
        self._order(hours_ago=50, status=Order.OrderStatus.shipping)

        self._run()

        self.assertEqual(len(mail.outbox), 0)

    def test_an_unpaid_order_is_left_alone(self):
        # Sin `paid_at` no hay reloj: el pedido se creo pero nunca se pago.
        Order.objects.create(amount=29500, status=Order.OrderStatus.not_processed)

        self._run()

        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ADMIN_NOTIFY_EMAILS=[])
    def test_with_no_channel_the_order_stays_unmarked(self):
        # Si no sale por ningun lado, no se marca como avisado: al configurar
        # el canal el aviso tiene que salir, no haberse perdido en silencio.
        order = self._order(hours_ago=50)

        self._run()

        order.refresh_from_db()
        self.assertIsNone(order.dispatch_warned_at)

    def test_dry_run_changes_nothing(self):
        order = self._order(hours_ago=50)

        output = self._run('--dry-run')

        self.assertIn(f'Order {order.id}', output)
        self.assertEqual(len(mail.outbox), 0)
        order.refresh_from_db()
        self.assertIsNone(order.dispatch_warned_at)

    def test_the_warning_also_pushes(self):
        admin = User.objects.create_superuser(
            email='duena@rayadito.cl', password='Testpass123',
            first_name='Duena', last_name='Rayadito',
        )
        DevicePushToken.objects.create(token='ExponentPushToken[abc]', user=admin)
        order = self._order(hours_ago=50)
        response = mock.Mock()
        response.json.return_value = {'data': [{'status': 'ok'}]}
        response.raise_for_status.return_value = None

        with mock.patch('notifications.expo.requests.post', return_value=response) as post:
            self._run()

        message = post.call_args.kwargs['json'][0]
        self.assertIn(f'#{order.id}', message['title'])
        self.assertEqual(message['data'],
                         {'type': 'pending_dispatch', 'order_id': order.id})

    def test_the_deadline_is_counted_from_the_payment(self):
        order = self._order(hours_ago=50)

        self.assertEqual(notify.dispatch_deadline(order),
                         order.paid_at + timedelta(hours=72))

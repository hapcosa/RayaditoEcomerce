"""Avisos al cliente por WhatsApp (Cloud API)."""
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from notifications import whatsapp, whatsapp_notices
from notifications.models import WhatsAppMessage, WhatsAppOptIn
from orders.models import Order, OrderItem
from payment import services
from payment.models import Payments
from product.models import Product
from shipping.models import Shipping

User = get_user_model()
S = Order.OrderStatus

WHATSAPP_ON = override_settings(
    WHATSAPP_ENABLED=True,
    WHATSAPP_PHONE_NUMBER_ID='123456789',
    WHATSAPP_ACCESS_TOKEN='EAAsecreto',
    WHATSAPP_GRAPH_VERSION='v23.0',
    WHATSAPP_TEMPLATE_LANGUAGE='es_CL',
    ADMIN_NOTIFY_EMAILS=[],
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def accepted(wamid='wamid.ABC'):
    return FakeResponse({
        'messaging_product': 'whatsapp',
        'contacts': [{'input': '56912345678', 'wa_id': '56912345678'}],
        'messages': [{'id': wamid, 'message_status': 'accepted'}],
    })


class NormalizePhoneTests(TestCase):
    def test_accepts_the_usual_ways_of_writing_a_chilean_mobile(self):
        for raw in ('912345678', '9 1234 5678', '+56 9 1234 5678',
                    '56912345678', '+56-9-1234-5678'):
            self.assertEqual(whatsapp.normalize_phone(raw), '56912345678', raw)

    def test_rejects_landlines_short_numbers_and_foreign_numbers(self):
        for raw in ('', None, '12345', '226543210', '+5622654321',
                    '+5491123456789', '812345678'):
            self.assertEqual(whatsapp.normalize_phone(raw), '', raw)


@WHATSAPP_ON
class SendTemplateTests(TestCase):
    def test_sends_named_parameters_with_bearer_token(self):
        with mock.patch('notifications.whatsapp.requests.post',
                        return_value=accepted()) as post:
            wamid = whatsapp.send_template(
                '56912345678', 'pedido_confirmado', {'nombre': 'Ana', 'total': 100})

        self.assertEqual(wamid, 'wamid.ABC')
        url = post.call_args.args[0]
        self.assertEqual(url, 'https://graph.facebook.com/v23.0/123456789/messages')
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs['headers'], {'Authorization': 'Bearer EAAsecreto'})
        body = kwargs['json']
        self.assertEqual(body['messaging_product'], 'whatsapp')
        self.assertEqual(body['to'], '56912345678')
        self.assertEqual(body['type'], 'template')
        self.assertEqual(body['template']['name'], 'pedido_confirmado')
        self.assertEqual(body['template']['language'], {'code': 'es_CL'})
        self.assertEqual(body['template']['components'], [{
            'type': 'body',
            'parameters': [
                {'type': 'text', 'parameter_name': 'nombre', 'text': 'Ana'},
                {'type': 'text', 'parameter_name': 'total', 'text': '100'},
            ],
        }])

    def test_a_template_without_parameters_has_no_components(self):
        with mock.patch('notifications.whatsapp.requests.post',
                        return_value=accepted()) as post:
            whatsapp.send_template('56912345678', 'hello_world', {}, language='en_US')

        template = post.call_args.kwargs['json']['template']
        self.assertNotIn('components', template)
        self.assertEqual(template['language'], {'code': 'en_US'})

    def test_a_meta_error_is_raised_with_its_details(self):
        error = FakeResponse({'error': {
            'message': '(#132000) Number of parameters does not match',
            'code': 132000,
            'error_data': {'details': 'body: expected 3, got 2'},
        }}, status_code=400)
        with mock.patch('notifications.whatsapp.requests.post', return_value=error):
            with self.assertRaisesMessage(whatsapp.WhatsAppError,
                                          'code 132000): body: expected 3'):
                whatsapp.send_template('56912345678', 'x', {})

    def test_the_token_never_ends_up_in_the_error(self):
        with mock.patch('notifications.whatsapp.requests.post',
                        side_effect=OSError('fallo con Bearer EAAsecreto')):
            with self.assertRaises(whatsapp.WhatsAppError) as ctx:
                whatsapp.send_template('56912345678', 'x', {})
        self.assertNotIn('EAAsecreto', str(ctx.exception))


class OrderFixtureMixin:
    def setUp(self):
        category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de plata', product_type='joya', description='Hecho a mano',
            price=25000, compare_price=0, category=category, photo='',
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

    def opt_in(self, phone='+56 9 1234 5678'):
        return whatsapp_notices.record_opt_in(
            self.order, phone, 'Acepto recibir avisos de mi pedido por WhatsApp.')


@WHATSAPP_ON
class PaidOrderNoticeTests(OrderFixtureMixin, APITestCase):
    def _approve(self, payment_id=4242, status_value='approved'):
        with self.captureOnCommitCallbacks(execute=True):
            return services.record_payment({
                'id': payment_id,
                'external_reference': str(self.order.id),
                'status': status_value,
                'status_detail': 'accredited',
                'installments': 1,
            })

    def test_an_approved_payment_sends_the_confirmation_once(self):
        self.opt_in()
        with mock.patch('notifications.whatsapp.requests.post',
                        return_value=accepted()) as post:
            self._approve()
            self._approve()

        self.assertEqual(post.call_count, 1)
        body = post.call_args.kwargs['json']
        self.assertEqual(body['to'], '56912345678')
        self.assertEqual(body['template']['name'], 'pedido_confirmado')
        params = {p['parameter_name']: p['text']
                  for p in body['template']['components'][0]['parameters']}
        # El numero que ve el cliente en /pedidos: el id del pago de MercadoPago.
        self.assertEqual(params, {'nombre': 'Ana', 'pedido': '4242',
                                  'total': '$54.500'})
        message = WhatsAppMessage.objects.get(order=self.order, key='paid_order')
        self.assertEqual(message.status, WhatsAppMessage.Status.SENT)
        self.assertEqual(message.wamid, 'wamid.ABC')

    def test_without_opt_in_nothing_is_sent(self):
        with mock.patch('notifications.whatsapp.requests.post') as post:
            self._approve()

        post.assert_not_called()
        self.assertFalse(WhatsAppMessage.objects.exists())

    def test_a_revoked_opt_in_is_respected(self):
        opt_in = self.opt_in()
        opt_in.revoked_at = timezone.now()
        opt_in.save()
        with mock.patch('notifications.whatsapp.requests.post') as post:
            self._approve()

        post.assert_not_called()

    @override_settings(WHATSAPP_ENABLED=False)
    def test_with_the_flag_off_nothing_is_sent(self):
        self.opt_in()
        with mock.patch('notifications.whatsapp.requests.post') as post:
            self._approve()

        post.assert_not_called()

    def test_a_rejected_payment_sends_nothing(self):
        self.opt_in()
        with mock.patch('notifications.whatsapp.requests.post') as post:
            self._approve(status_value='rejected')

        post.assert_not_called()

    def test_a_whatsapp_failure_does_not_break_the_sale(self):
        self.opt_in()
        with mock.patch('notifications.whatsapp.requests.post',
                        side_effect=OSError('sin red')):
            payment = self._approve()

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, S.processed)
        self.assertEqual(payment.status, Payments.PaymentStatus.APPROVED)
        message = WhatsAppMessage.objects.get(order=self.order)
        self.assertEqual(message.status, WhatsAppMessage.Status.FAILED)
        self.assertIn('sin red', message.error)

    def test_a_database_error_in_the_notice_does_not_break_the_webhook(self):
        self.opt_in()
        with mock.patch('notifications.whatsapp_notices.send_order_notice',
                        side_effect=RuntimeError('boom')):
            payment = self._approve()

        self.assertEqual(payment.status, Payments.PaymentStatus.APPROVED)


@WHATSAPP_ON
class ShippedNoticeTests(OrderFixtureMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser(
            email='admin@rayadito.cl', password='Testpass123',
            first_name='Admin', last_name='Rayadito',
        )
        self.client.force_authenticate(self.admin)
        self.order.status = S.processed
        self.order.save(update_fields=['status'])
        self.opt_in()

    def _params(self, post):
        body = post.call_args.kwargs['json']
        self.assertEqual(body['template']['name'], 'pedido_despachado')
        return {p['parameter_name']: p['text']
                for p in body['template']['components'][0]['parameters']}

    def test_marking_as_shipped_in_the_admin_app_sends_the_tracking_number(self):
        with mock.patch('notifications.whatsapp.requests.post',
                        return_value=accepted()) as post:
            with self.captureOnCommitCallbacks(execute=True):
                res = self.client.patch(
                    f'/api/admin/orders/{self.order.id}/status/',
                    {'status': S.shipping, 'deliveryNumber': 'OF-998877'},
                    format='json',
                )

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(self._params(post), {
            'nombre': 'Ana', 'pedido': str(self.order.id),
            'envio': 'Starken', 'seguimiento': 'OF-998877',
        })

    def test_other_status_changes_send_nothing(self):
        with mock.patch('notifications.whatsapp.requests.post') as post:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.patch(f'/api/admin/orders/{self.order.id}/status/',
                                  {'status': S.cancelled}, format='json')

        post.assert_not_called()

    def test_correcting_the_number_in_the_legacy_view_does_not_resend(self):
        with mock.patch('notifications.whatsapp.requests.post',
                        return_value=accepted()) as post:
            for number in ('OF-1', 'OF-2'):
                with self.captureOnCommitCallbacks(execute=True):
                    self.client.post(f'/api/orders/dispatch/{self.order.id}',
                                     {'deliveryNumber': number}, format='json')

        self.assertEqual(post.call_count, 1)
        self.assertEqual(self._params(post)['seguimiento'], 'OF-1')


class OptInTests(OrderFixtureMixin, TestCase):
    def test_stores_the_normalized_phone_and_the_accepted_text(self):
        opt_in = self.opt_in('9 1234 5678')

        self.assertEqual(opt_in.phone, '56912345678')
        self.assertIn('WhatsApp', opt_in.consent_text)
        self.assertTrue(opt_in.is_active)

    def test_an_invalid_phone_stores_nothing(self):
        self.assertIsNone(self.opt_in('226543210'))
        self.assertFalse(WhatsAppOptIn.objects.exists())


class WhatsAppTestCommandTests(TestCase):
    @WHATSAPP_ON
    def test_sends_hello_world_by_default(self):
        out = StringIO()
        with mock.patch('notifications.whatsapp.requests.post',
                        return_value=accepted('wamid.T')) as post:
            call_command('whatsapp_test', '+56912345678', stdout=out)

        template = post.call_args.kwargs['json']['template']
        self.assertEqual(template['name'], 'hello_world')
        self.assertEqual(template['language'], {'code': 'en_US'})
        self.assertIn('wamid.T', out.getvalue())

    @override_settings(WHATSAPP_PHONE_NUMBER_ID='', WHATSAPP_ACCESS_TOKEN='')
    def test_without_credentials_it_explains_what_is_missing(self):
        with self.assertRaisesMessage(CommandError, 'WHATSAPP_PHONE_NUMBER_ID'):
            call_command('whatsapp_test', '+56912345678')

"""Documentos tributarios: RUT, modos de emision y datos de factura del checkout."""
import os
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APITestCase

from billing import rut, services
from billing.models import InvoiceRequest, TaxDocument
from billing.providers import BillingError, BillingProvider, IssuedDocument
from category.models import Category
from orders.models import Order, OrderItem
from payment import services as payment_services
from payment.models import Payments
from payment.tests import FakeMercadoPagoSDK
from product.models import Product
from shipping.models import Shipping

INVOICE = {
    'rut': '76.354.771-K', 'business_name': 'Taller Ejemplo SpA',
    'activity': 'Venta al por menor', 'address': 'Calle 1 123', 'commune': 'Ancud',
    'email': 'pagos@ejemplo.cl',
}


class RutTests(SimpleTestCase):
    def test_valid_ruts_are_normalized(self):
        self.assertEqual(rut.normalize('76.354.771-k'), '76354771-K')
        self.assertEqual(rut.normalize('11111111-1'), '11111111-1')
        self.assertEqual(rut.normalize(' 12.345.678-5 '), '12345678-5')
        self.assertEqual(rut.normalize('1-9'), '1-9')

    def test_invalid_ruts_are_rejected(self):
        for value in ('76.354.771-1', '12345678-0', '', 'abc', '123456789-0', 'K'):
            self.assertIsNone(rut.normalize(value), value)

    def test_pretty(self):
        self.assertEqual(rut.pretty('76354771-K'), '76.354.771-K')


class FakeProvider(BillingProvider):
    name = 'fake'
    calls = []
    fail = False

    def issue(self, document, order, items, invoice=None):
        FakeProvider.calls.append((document.kind, order.id, len(items), invoice))
        if FakeProvider.fail:
            raise BillingError('folios agotados')
        return IssuedDocument(folio='1001', external_id='ext-1',
                              pdf_url='https://proveedor.test/1001.pdf')


@override_settings(
    ADMIN_NOTIFY_EMAILS=['duena@rayadito.cl'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    BILLING_PROVIDER='billing.tests.FakeProvider',
    BILLING_INVOICES_ENABLED=True,
)
class OnOrderPaidTests(TestCase):
    def setUp(self):
        FakeProvider.calls = []
        FakeProvider.fail = False
        category = Category.objects.create(name='Anillos', ProductType='Joya')
        product = Product.objects.create(
            name='Anillo', product_type='joya', description='x', price=25000,
            compare_price=0, category=category, photo='')
        self.order = Order.objects.create(email='ana@cliente.cl', amount=29500,
                                          shipping_price=4500, transaction_id='1305512')
        OrderItem.objects.create(order=self.order, product=product, name='Anillo',
                                 price=25000, count=1)

    def ask_invoice(self):
        data, errors = services.parse_invoice_request(INVOICE)
        self.assertIsNone(errors)
        services.attach_invoice_request(self.order, data)

    @override_settings(BILLING_MODE='off')
    def test_off_records_nothing(self):
        self.assertIsNone(services.on_order_paid(self.order))
        self.assertFalse(TaxDocument.objects.exists())

    @override_settings(BILLING_MODE='voucher')
    def test_voucher_mode_records_mercadopago_receipt_as_issued(self):
        document = services.on_order_paid(self.order)
        self.assertEqual(document.kind, TaxDocument.Kind.VOUCHER)
        self.assertEqual(document.status, TaxDocument.Status.ISSUED)
        self.assertEqual(document.external_id, '1305512')
        self.assertEqual(document.amount, 29500)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(BILLING_MODE='voucher')
    def test_voucher_mode_invoice_is_pending_and_owner_is_told(self):
        self.ask_invoice()
        document = services.on_order_paid(self.order)
        self.assertEqual(document.kind, TaxDocument.Kind.FACTURA)
        self.assertEqual(document.status, TaxDocument.Status.PENDING)
        self.assertEqual(document.provider, 'manual')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('76.354.771-K', mail.outbox[0].body)
        self.assertIn('Taller Ejemplo SpA', mail.outbox[0].body)

    @override_settings(BILLING_MODE='voucher')
    def test_repeated_approval_creates_one_document(self):
        services.on_order_paid(self.order)
        services.on_order_paid(self.order)
        self.assertEqual(TaxDocument.objects.count(), 1)

    @override_settings(BILLING_MODE='provider')
    def test_provider_mode_issues_boleta(self):
        document = services.on_order_paid(self.order)
        self.assertEqual(document.kind, TaxDocument.Kind.BOLETA)
        self.assertEqual(document.status, TaxDocument.Status.ISSUED)
        self.assertEqual(document.folio, '1001')
        self.assertEqual(document.provider, 'fake')
        self.assertEqual(FakeProvider.calls, [('boleta', self.order.id, 1, None)])

    @override_settings(BILLING_MODE='provider')
    def test_provider_mode_issues_factura_with_invoice_data(self):
        self.ask_invoice()
        services.on_order_paid(self.order)
        kind, _, _, invoice = FakeProvider.calls[0]
        self.assertEqual(kind, 'factura')
        self.assertEqual(invoice.rut, '76354771-K')

    @override_settings(BILLING_MODE='provider')
    def test_provider_failure_is_recorded_and_retried(self):
        FakeProvider.fail = True
        document = services.on_order_paid(self.order)
        self.assertEqual(document.status, TaxDocument.Status.FAILED)
        self.assertEqual(document.last_error, 'folios agotados')

        FakeProvider.fail = False
        out = StringIO()
        call_command('issue_tax_documents', stdout=out)
        self.assertIn('Issued 1 of 1', out.getvalue())
        document.refresh_from_db()
        self.assertEqual(document.status, TaxDocument.Status.ISSUED)

    @override_settings(BILLING_MODE='provider', BILLING_PROVIDER='')
    def test_missing_provider_fails_the_document_not_the_sale(self):
        document = services.on_order_paid(self.order)
        self.assertEqual(document.status, TaxDocument.Status.FAILED)
        self.assertIn('BILLING_PROVIDER', document.last_error)

    @override_settings(BILLING_MODE='voucher')
    def test_approved_payment_registers_the_document_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            payment_services.record_payment({
                'id': 1305512, 'external_reference': str(self.order.id),
                'status': 'approved', 'status_detail': 'accredited', 'installments': 1,
            })
        self.assertEqual(TaxDocument.objects.get().kind, TaxDocument.Kind.VOUCHER)

    @override_settings(BILLING_MODE='voucher')
    def test_billing_crash_does_not_break_the_payment(self):
        with mock.patch('billing.services.on_order_paid', side_effect=RuntimeError('boom')):
            with self.captureOnCommitCallbacks(execute=True):
                payment = payment_services.record_payment({
                    'id': 1305512, 'external_reference': str(self.order.id),
                    'status': 'approved', 'status_detail': 'accredited', 'installments': 1,
                })
        self.assertEqual(payment.status, Payments.PaymentStatus.APPROVED)


class ParseInvoiceTests(SimpleTestCase):
    @override_settings(BILLING_MODE='voucher', BILLING_INVOICES_ENABLED=True)
    def test_errors_per_field(self):
        data, errors = services.parse_invoice_request({'rut': '1-1'})
        self.assertIsNone(data)
        self.assertEqual(set(errors), {'rut', 'business_name', 'activity', 'address', 'commune'})

    @override_settings(BILLING_MODE='off', BILLING_INVOICES_ENABLED=True)
    def test_ignored_while_billing_is_off(self):
        self.assertEqual(services.parse_invoice_request(INVOICE), (None, None))

    @override_settings(BILLING_MODE='voucher', BILLING_INVOICES_ENABLED=False)
    def test_ignored_when_invoices_disabled(self):
        self.assertEqual(services.parse_invoice_request(INVOICE), (None, None))


@override_settings(BILLING_MODE='voucher', BILLING_INVOICES_ENABLED=True)
class CheckoutInvoiceTests(APITestCase):
    def setUp(self):
        category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo', product_type='joya', description='x', price=25000,
            compare_price=0, category=category, photo='')
        self.shipping = Shipping.objects.create(
            name='Starken', time_to_delivery='3 días', description='x', price=4500, photo='')

    def pay(self, invoice):
        fake_sdk = FakeMercadoPagoSDK(preference_response={'id': 'pref', 'init_point': 'x'})
        with mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}), \
                mock.patch('payment.services.mercadopago_sdk', return_value=fake_sdk):
            return self.client.post('/api/payment/make-payment', {
                'shipping_id': self.shipping.id, 'email': 'ana@cliente.cl',
                'first_name': 'Ana', 'last_name': 'Ríos', 'address_line_1': 'Calle 1',
                'city': 'Ancud', 'state_province_region': 'Los Lagos',
                'telephone_number': '912345678',
                'items': [{'product': {'id': self.product.id}, 'count': 1}],
                'invoice': invoice,
            }, format='json')

    def test_guest_checkout_saves_invoice_data(self):
        response = self.pay(INVOICE)
        self.assertEqual(response.status_code, 200, response.data)
        invoice = InvoiceRequest.objects.get(order_id=response.data['order_id'])
        self.assertEqual(invoice.rut, '76354771-K')

    def test_invalid_invoice_creates_no_order(self):
        response = self.pay({**INVOICE, 'rut': '76.354.771-1'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('rut', response.data['invoice'])
        self.assertFalse(Order.objects.exists())

    def test_without_invoice_nothing_is_saved(self):
        self.assertEqual(self.pay(None).status_code, 200)
        self.assertFalse(InvoiceRequest.objects.exists())

    def test_config_endpoint(self):
        response = self.client.get('/api/billing/config')
        self.assertEqual(response.data, {'mode': 'voucher', 'invoices_enabled': True})

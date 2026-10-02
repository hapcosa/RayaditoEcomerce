"""Integracion con Starken: cliente, precios, checkout, pago, emision y seguimiento.

Ningun test sale a la red: `requests.request` se reemplaza por respuestas con
la forma documentada en developers.starken.cl (y verificada contra su QA).
"""
import os
from io import StringIO
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from orders.models import Order
from product.models import Product, ProductVariant
from shipping import pricing, starken
from shipping.models import Shipment, Shipping
from shipping.shipments import create_shipment, sync_tracking

User = get_user_model()

STARKEN_ON = {
    'ENABLED': True,
    'API_URL': 'https://starken.test/rest',
    'RUT': '76211240',
    'CLAVE': 'key',
    'ORIGIN_CITY': 388,
    'CTA_CTE': '',
    'CTA_CTE_DV': '',
    'CENTRO_COSTO': '0',
    'PARCEL_KG': 1.0,
    'PARCEL_CM': [20.0, 15.0, 10.0],
    'EMISSION_URL': 'https://emision.test/h2h',
    'EMITTER_COMPANY_RUT': '76211240',
    'EMITTER_USER_RUT': '10',
    'EMITTER_PASSWORD': 'secreto',
    'SENDER_RUT': '76.211.240-K',
    'SENDER_NAME': 'Piedras Rayadito',
    'SENDER_STREET': 'Blanco Encalada',
    'SENDER_NUMBER': '123',
    'SENDER_COMMUNE': 'Castro',
    'SENDER_PHONE': '+56 9 1234 5678',
    'SENDER_EMAIL': 'contacto@piedrasdelrayadito.cl',
    'CONTENT': 'ARTESANIA',
    'TIMEOUT': 5,
}
STARKEN_OFF = {**STARKEN_ON, 'ENABLED': False}

CITIES = {
    'type': 'listarCiudadesDestinoRespuesta',
    'codigoRespuesta': 1,
    'listaCiudadesDestino': [
        {'codigoCiudad': 1, 'nombreCiudad': 'SANTIAGO',
         'listaComunas': [{'codigoComuna': 1, 'nombreComuna': 'NUNOA'},
                          {'codigoComuna': 2, 'nombreComuna': 'PROVIDENCIA'}]},
        {'codigoCiudad': 389, 'nombreCiudad': 'ANCUD',
         'listaComunas': [{'codigoComuna': 3, 'nombreComuna': 'ANCUD'}]},
        {'codigoCiudad': 1300, 'nombreCiudad': 'PUERTO NATALES',
         'listaComunas': [{'codigoComuna': 4, 'nombreComuna': 'PUERTO NATALES'}]},
    ],
}


def rates(domicilio=6990.0, agencia=6650.0):
    return {
        'type': 'consultarCoberturaRespuesta',
        'codigoRespuesta': 1,
        'mensajeRespuesta': 'Busqueda exitosa.',
        'listaTarifas': [
            {'costoTotal': agencia, 'diasEntrega': 2,
             'tipoEntrega': {'codigoTipoEntrega': 1, 'descripcionTipoEntrega': 'AGENCIA'},
             'tipoServicio': {'codigoTipoServicio': 0, 'descripcionTipoServicio': 'NORMAL'}},
            {'costoTotal': domicilio, 'diasEntrega': 2,
             'tipoEntrega': {'codigoTipoEntrega': 2, 'descripcionTipoEntrega': 'DOMICILIO'},
             'tipoServicio': {'codigoTipoServicio': 0, 'descripcionTipoServicio': 'NORMAL'}},
        ],
    }


def fake_response(payload, status_code=200):
    response = mock.Mock(status_code=status_code)
    response.json.return_value = payload
    return response


class FakeStarken:
    """Responde por URL, como el servidor real, y anota lo que se le pidio."""

    def __init__(self, quote=None, cities=CITIES, tracking=None, emission=None):
        self.routes = {
            'listarCiudadesDestino': cities,
            'consultarTarifas': quote or rates(),
            'getDetalleSeguimientoNuevo': tracking,
            'h2h': emission,
        }
        self.calls = []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        for suffix, payload in self.routes.items():
            if url.endswith(suffix):
                if isinstance(payload, Exception):
                    raise payload
                return fake_response(payload)
        return fake_response({}, 404)

    def count(self, suffix):
        return sum(1 for _, url, _ in self.calls if url.endswith(suffix))


def patch_http(fake):
    return mock.patch('shipping.starken.requests.request', side_effect=fake)


@override_settings(STARKEN=STARKEN_ON)
class StarkenClientTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_quote_returns_integer_clp_for_the_delivery_type(self):
        fake = FakeStarken()
        with patch_http(fake):
            self.assertEqual(starken.quote('Ñuñoa', delivery_type=2), 6990)
            self.assertEqual(starken.quote('Ñuñoa', delivery_type=1), 6650)

        _, _, kwargs = [c for c in fake.calls if c[1].endswith('consultarTarifas')][0]
        self.assertEqual(kwargs['headers']['Rut'], '76211240')
        self.assertEqual(kwargs['json']['codigoCiudadOrigen'], 388)
        self.assertEqual(kwargs['json']['codigoCiudadDestino'], 1)
        self.assertEqual(kwargs['json']['kilos'], 1.0)
        self.assertEqual(kwargs['json']['rutCliente'], '1')

    def test_quotes_and_cities_are_cached(self):
        fake = FakeStarken()
        with patch_http(fake):
            starken.quote('Ancud', 2)
            starken.quote('Ancud', 2)

        self.assertEqual(fake.count('listarCiudadesDestino'), 1)
        self.assertEqual(fake.count('consultarTarifas'), 1)

    @override_settings(STARKEN={**STARKEN_ON, 'CTA_CTE': '19154', 'CTA_CTE_DV': 'K'})
    def test_current_account_rate_is_used_when_configured(self):
        fake = FakeStarken()
        with patch_http(fake):
            starken.quote('Ancud', 2)

        body = [c for c in fake.calls if c[1].endswith('consultarTarifas')][0][2]['json']
        self.assertEqual((body['cuentaCorriente'], body['cuentaCorrienteDV']), ('19154', 'K'))
        self.assertEqual(body['rutCliente'], '')

    def test_half_pesos_round_up(self):
        with patch_http(FakeStarken(quote=rates(domicilio=6990.5))):
            self.assertEqual(starken.quote('Ancud', 2), 6991)

    def test_communes_with_another_name_in_starken(self):
        with patch_http(FakeStarken()):
            self.assertEqual(starken.city_code_for('Natales'), 1300)
            self.assertEqual(starken.city_code_for('ñuñoa'), 1)

    def test_commune_outside_coverage_is_an_error(self):
        with patch_http(FakeStarken()):
            with self.assertRaisesMessage(starken.StarkenError, 'no llega'):
                starken.quote('Isla de Pascua', 2)

    def test_missing_delivery_combination_is_an_error(self):
        with patch_http(FakeStarken()):
            with self.assertRaises(starken.StarkenError):
                starken.quote('Ancud', 2, service_type=1)

    def test_http_errors_and_timeouts_become_starken_errors(self):
        with mock.patch('shipping.starken.requests.request',
                        return_value=fake_response({}, 500)):
            with self.assertRaisesMessage(starken.StarkenError, 'HTTP 500'):
                starken.destination_cities()
        with mock.patch('shipping.starken.requests.request',
                        side_effect=requests.Timeout()):
            with self.assertRaisesMessage(starken.StarkenError, 'Timeout'):
                starken.destination_cities()

    @override_settings(STARKEN={**STARKEN_ON, 'ORIGIN_CITY': 0})
    def test_origin_city_is_required(self):
        with self.assertRaisesMessage(starken.StarkenError, 'STARKEN_ORIGIN_CITY'):
            starken.quote('Ancud', 2)

    def test_tracking_detects_final_statuses(self):
        with patch_http(FakeStarken(tracking={'estadoFlete': 'EN TRANSITO'})):
            self.assertEqual(starken.tracking_status('222582291'), ('EN TRANSITO', False))
        with patch_http(FakeStarken(tracking={'estadoFlete': 'ENTREGADO'})):
            self.assertEqual(starken.tracking_status('222582291'), ('ENTREGADO', True))

    def test_freight_number_in_scientific_notation(self):
        self.assertEqual(starken.parse_freight_number('2.22746632E8'), '222746632')
        self.assertEqual(starken.parse_freight_number(222746632), '222746632')
        with self.assertRaises(starken.StarkenError):
            starken.parse_freight_number('2.5')

    def test_street_and_number_are_split(self):
        self.assertEqual(starken.split_street('Los Carrera 1234 depto 5'),
                         ('Los Carrera', '1234', 'depto 5'))
        self.assertEqual(starken.split_street('Av. Matta, 512B'), ('Av. Matta', '512B', ''))
        self.assertEqual(starken.split_street('Parcela El Bosque'),
                         ('Parcela El Bosque', 'S/N', ''))

    def test_rut_is_split_into_number_and_dv(self):
        self.assertEqual(starken.split_rut('76.211.240-k'), ('76211240', 'K'))
        with self.assertRaises(starken.StarkenError):
            starken.split_rut('76211240')


class ShopFixtures:
    def make_catalog(self):
        category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = Product.objects.create(
            name='Anillo de plata', product_type='joya', description='Hecho a mano',
            price=25000, compare_price=0, category=category, photo='')
        ProductVariant.objects.create(product=self.product, sku='ANI-1', stock=5)
        self.retiro = Shipping.objects.create(
            name='Retiro en taller', time_to_delivery='1 día', description='-', price=0)
        self.domicilio = Shipping.objects.create(
            name='Starken a domicilio', time_to_delivery='2 días', description='-',
            price=999, carrier=Shipping.Carrier.starken,
            starken_delivery_type=Shipping.DeliveryType.home)
        self.agencia = Shipping.objects.create(
            name='Starken en agencia', time_to_delivery='2 días', description='-',
            price=999, carrier=Shipping.Carrier.starken,
            starken_delivery_type=Shipping.DeliveryType.agency)


class ShippingOptionsTests(ShopFixtures, APITestCase):
    def setUp(self):
        cache.clear()
        self.make_catalog()

    def names(self, response):
        return [(o['name'], o['price']) for o in response.data['shipping_options']]

    @override_settings(STARKEN=STARKEN_OFF)
    def test_disabled_offers_only_fixed_price_options(self):
        res = self.client.get('/api/shipp/get-shipping-options', {'comuna': 'Ancud'})

        self.assertEqual(self.names(res), [('Retiro en taller', 0)])

    @override_settings(STARKEN=STARKEN_ON)
    def test_enabled_quotes_starken_options_for_the_commune(self):
        with patch_http(FakeStarken()):
            res = self.client.get('/api/shipp/get-shipping-options', {'comuna': 'Ancud'})

        self.assertEqual(self.names(res), [
            ('Retiro en taller', 0),
            ('Starken en agencia', 6650),
            ('Starken a domicilio', 6990),
        ])

    @override_settings(STARKEN=STARKEN_ON)
    def test_without_commune_starken_is_left_out(self):
        fake = FakeStarken()
        with patch_http(fake):
            res = self.client.get('/api/shipp/get-shipping-options')

        self.assertEqual(self.names(res), [('Retiro en taller', 0)])
        self.assertEqual(fake.calls, [])

    @override_settings(STARKEN=STARKEN_ON)
    def test_starken_down_keeps_the_checkout_working(self):
        with mock.patch('shipping.starken.requests.request',
                        side_effect=requests.ConnectionError()):
            res = self.client.get('/api/shipp/get-shipping-options', {'comuna': 'Ancud'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.names(res), [('Retiro en taller', 0)])

    @override_settings(STARKEN=STARKEN_ON)
    def test_quote_endpoint_uses_the_same_prices(self):
        with patch_http(FakeStarken()):
            res = self.client.post('/api/shipp/quote', {'comuna': 'Ancud'}, format='json')

        self.assertEqual(res.data['source'], 'starken')
        self.assertIn(('Starken a domicilio', 6990), self.names(res))


@mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
class StarkenPaymentTests(ShopFixtures, APITestCase):
    """El precio del envio que se cobra lo cotiza el servidor, no el navegador."""

    def setUp(self):
        cache.clear()
        self.make_catalog()

    def pay_as_guest(self, shipping, city='Ancud', **extra):
        from payment.tests import FakeMercadoPagoSDK
        self.sdk = FakeMercadoPagoSDK(preference_response={'id': 'pref'})
        with mock.patch('payment.services.mercadopago_sdk', return_value=self.sdk):
            return self.client.post('/api/payment/make-payment', {
                'shipping_id': shipping.id,
                'email': 'invitada@rayadito.cl',
                'first_name': 'Ines', 'last_name': 'Perez',
                'address_line_1': 'Calle 2 123', 'city': city,
                'state_province_region': 'Los Lagos', 'postal_zip_code': '',
                'telephone_number': '912345678',
                'items': [{'product': {'id': self.product.id}, 'count': 1}],
                **extra,
            }, format='json')

    @override_settings(STARKEN=STARKEN_ON)
    def test_starken_price_is_quoted_for_the_order_commune(self):
        with patch_http(FakeStarken()):
            res = self.pay_as_guest(self.domicilio, price=1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        order = Order.objects.get(id=res.data['order_id'])
        self.assertEqual(order.shipping_price, 6990)
        self.assertEqual(order.amount, 25000 + 6990)
        items = self.sdk.preference_client.created_payload['items']
        self.assertEqual([i['unit_price'] for i in items], [25000, 6990])

    @override_settings(STARKEN=STARKEN_ON)
    def test_unquotable_starken_option_does_not_create_an_order(self):
        with mock.patch('shipping.starken.requests.request',
                        side_effect=requests.ConnectionError()):
            res = self.pay_as_guest(self.domicilio)

        self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(Order.objects.exists())

    @override_settings(STARKEN=STARKEN_OFF)
    def test_starken_option_cannot_be_paid_while_disabled(self):
        # Sin cotizacion no hay precio: cobrar el `price` de respaldo (999)
        # seria cobrar un numero inventado.
        res = self.pay_as_guest(self.domicilio)

        self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(Order.objects.exists())

    @override_settings(STARKEN=STARKEN_ON)
    def test_fixed_price_options_never_call_starken(self):
        fake = FakeStarken()
        with patch_http(fake):
            res = self.pay_as_guest(self.retiro)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Order.objects.get().shipping_price, 0)
        self.assertEqual(fake.calls, [])


STARKEN_EMIT = {**STARKEN_ON, 'CTA_CTE': '19154', 'CTA_CTE_DV': 'K'}


@override_settings(STARKEN=STARKEN_EMIT)
class EmissionTests(ShopFixtures, TestCase):
    def setUp(self):
        cache.clear()
        self.make_catalog()
        self.order = Order.objects.create(
            amount=25000 + 6990, shipping_price=6990, full_name='Ines Perez Soto',
            email='invitada@rayadito.cl', address_line_1='Los Carrera 1234 depto 5',
            city='Ñuñoa', telephone_number='912345678', shipping_id=self.domicilio,
            paid_at=timezone.now(), status=Order.OrderStatus.processed)

    def test_payload_follows_the_h2h_dictionary(self):
        payload = starken.emission_payload(self.order)

        self.assertEqual(payload['tipoEntrega'], 2)
        self.assertEqual(payload['tipoPago'], 2)
        self.assertEqual(payload['comunaDestino'], 'NUNOA')
        self.assertEqual(payload['direccionDestinatario'], 'Los Carrera')
        self.assertEqual(payload['numeracionDireccionDestinatario'], '1234')
        self.assertEqual(payload['nombreRazonSocialDestinatario'], 'Ines')
        self.assertEqual(payload['apellidoPaternoDestinatario'], 'Perez')
        self.assertEqual(payload['valorDeclarado'], 25000)
        self.assertEqual((payload['rutRemitente'], payload['dvRemitente']), ('76211240', 'K'))
        self.assertEqual(payload['tipoEncargo1'], 29)
        self.assertEqual((payload['numeroCtaCte'], payload['dvNumeroCtaCte']), ('19154', 'K'))

    def test_agency_delivery_needs_the_agency_code(self):
        self.order.shipping_id = self.agencia
        with self.assertRaisesMessage(starken.StarkenError, 'codigo de agencia'):
            starken.emission_payload(self.order)
        self.assertEqual(
            starken.emission_payload(self.order, agency_code=1467)['comunaDestino'], '@1467')

    def test_high_declared_value_needs_the_boleta(self):
        self.order.amount = 80000 + 6990
        with self.assertRaisesMessage(starken.StarkenError, '--boleta'):
            starken.emission_payload(self.order)
        payload = starken.emission_payload(self.order, document_number='1234')
        self.assertEqual((payload['tipoDocumento1'], payload['numeroDocumento1']), (28, '1234'))

    @override_settings(STARKEN={**STARKEN_EMIT, 'EMITTER_PASSWORD': '', 'SENDER_RUT': ''})
    def test_missing_settings_are_listed(self):
        with self.assertRaisesMessage(starken.StarkenError, 'STARKEN_EMITTER_PASSWORD'):
            starken.emission_payload(self.order)

    def test_create_shipment_saves_the_tracking_number(self):
        fake = FakeStarken(emission={'codigoError': 0, 'DescripcionError': 'OK',
                                     'nroOrdenFlete': '2.22746632E8'})
        with patch_http(fake):
            shipment = create_shipment(self.order)

        self.order.refresh_from_db()
        self.assertEqual(shipment.tracking_number, '222746632')
        self.assertEqual(self.order.deliveryNumber, '222746632')
        # Emitir no es despachar: el estado lo sigue cambiando la duena.
        self.assertEqual(self.order.status, Order.OrderStatus.processed)

    def test_rejected_emission_saves_nothing(self):
        fake = FakeStarken(emission={'codigoError': 12, 'DescripcionError': 'Comuna invalida'})
        with patch_http(fake):
            with self.assertRaisesMessage(starken.StarkenError, 'Comuna invalida'):
                create_shipment(self.order)

        self.assertFalse(Shipment.objects.exists())
        self.order.refresh_from_db()
        self.assertIsNone(self.order.deliveryNumber)

    def test_unpaid_or_already_emitted_orders_are_refused(self):
        Shipment.objects.create(order=self.order, tracking_number='1')
        with self.assertRaisesMessage(starken.StarkenError, 'ya tiene la OF'):
            create_shipment(self.order)
        self.order.paid_at = None
        with self.assertRaisesMessage(starken.StarkenError, 'no esta pagado'):
            create_shipment(self.order)

    def test_dry_run_hides_the_password(self):
        out = StringIO()
        call_command('starken_emit', self.order.id, '--dry-run', stdout=out)

        self.assertIn('claveUsuarioEmisor: ***', out.getvalue())
        self.assertNotIn('secreto', out.getvalue())

    @override_settings(STARKEN=STARKEN_OFF)
    def test_command_refuses_when_disabled(self):
        with self.assertRaises(CommandError):
            call_command('starken_emit', self.order.id)


@override_settings(STARKEN=STARKEN_ON)
class TrackingSyncTests(ShopFixtures, TestCase):
    def setUp(self):
        cache.clear()
        self.make_catalog()
        self.order = Order.objects.create(
            amount=31990, shipping_price=6990, shipping_id=self.domicilio,
            status=Order.OrderStatus.shipping, deliveryNumber='222582291',
            paid_at=timezone.now())

    def test_manually_entered_tracking_number_is_followed(self):
        with patch_http(FakeStarken(tracking={'estadoFlete': 'EN TRANSITO'})):
            self.assertEqual(sync_tracking(), (1, 0))

        shipment = Shipment.objects.get(order=self.order)
        self.assertEqual((shipment.status, shipment.is_final), ('EN TRANSITO', False))

    def test_final_status_stops_the_polling(self):
        with patch_http(FakeStarken(tracking={'estadoFlete': 'ENTREGADO'})):
            sync_tracking()
        fake = FakeStarken(tracking={'estadoFlete': 'ENTREGADO'})
        with patch_http(fake):
            self.assertEqual(sync_tracking(), (0, 0))

        self.assertEqual(fake.calls, [])
        self.assertTrue(Shipment.objects.get().is_final)

    def test_errors_are_recorded_and_do_not_stop_the_run(self):
        Order.objects.create(
            amount=1, shipping_id=self.domicilio, status=Order.OrderStatus.shipping,
            deliveryNumber='no-es-numero')
        with patch_http(FakeStarken(tracking={'estadoFlete': 'EN DESTINO'})):
            self.assertEqual(sync_tracking(), (1, 1))

        self.assertIn('no numerico', Shipment.objects.get(tracking_number='no-es-numero').last_error)

    def test_fixed_price_orders_are_not_tracked(self):
        self.order.shipping_id = self.retiro
        self.order.save()
        fake = FakeStarken()
        with patch_http(fake):
            self.assertEqual(sync_tracking(), (0, 0))
        self.assertEqual(fake.calls, [])

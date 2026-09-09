from io import StringIO

from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from shipping.models import Shipping


class ShippingLocationsTests(APITestCase):
    def test_locations_returns_chile_regions_and_communes(self):
        response = self.client.get('/api/shipp/locations')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 16)
        self.assertEqual(response.data['total_communes'], 346)
        self.assertEqual(response.data['regions'][0]['name'], 'Arica y Parinacota')

    def test_locations_filters_region_by_name(self):
        response = self.client.get('/api/shipp/locations?region=Los%20Lagos')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        region = response.data['region']
        self.assertEqual(region['number'], 10)
        self.assertEqual(region['communes_count'], 30)
        self.assertIn('Ancud', region['communes'])
        self.assertIn('Castro', region['communes'])
        self.assertIn('Quellón', region['communes'])

    def test_locations_filters_region_without_accents_or_by_number(self):
        response = self.client.get('/api/shipp/locations?region=Tarapaca')
        by_number = self.client.get('/api/shipp/locations?region=10')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['region']['name'], 'Tarapacá')
        self.assertEqual(by_number.status_code, status.HTTP_200_OK)
        self.assertEqual(by_number.data['region']['name'], 'Los Lagos')

    def test_locations_unknown_region_returns_404(self):
        response = self.client.get('/api/shipp/locations?region=Atlantida')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShippingQuoteTests(APITestCase):
    def setUp(self):
        self.pickup = Shipping.objects.create(
            name='Retiro en taller',
            time_to_delivery='Mismo dia',
            description='Retiro coordinado en taller.',
            price=0,
            photo='',
        )
        self.delivery = Shipping.objects.create(
            name='Envio manual Chiloe',
            time_to_delivery='2 a 4 dias habiles',
            description='Despacho manual con operador disponible.',
            price=4500,
            photo='',
        )

    def test_shipping_price_is_integer_clp(self):
        self.delivery.refresh_from_db()

        self.assertIsInstance(self.delivery.price, int)
        self.assertEqual(self.delivery.price, 4500)

    def test_quote_returns_manual_options_ordered_by_price(self):
        response = self.client.post(
            '/api/shipp/quote',
            {'region': 'Los Lagos', 'comuna': 'Ancud'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source'], 'manual')
        self.assertEqual(response.data['destination'], {
            'region': 'Los Lagos',
            'comuna': 'Ancud',
        })
        self.assertEqual(
            [option['id'] for option in response.data['shipping_options']],
            [self.pickup.id, self.delivery.id],
        )
        self.assertEqual(
            [option['price'] for option in response.data['shipping_options']],
            [0, 4500],
        )

    def test_quote_accepts_city_as_destination(self):
        response = self.client.post(
            '/api/shipp/quote',
            {'city': 'Castro'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['destination'], {'city': 'Castro'})

    def test_quote_requires_destination(self):
        response = self.client.post('/api/shipp/quote', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)


class ShippingCatalogTests(APITestCase):
    def test_sin_opciones_devuelve_lista_vacia(self):
        """Catálogo vacío no es un error: el checkout tiene que poder distinguir
        "no hay opciones cargadas" de "la ruta no responde"."""
        response = self.client.get('/api/shipp/get-shipping-options')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shipping_options'], [])

    def test_lista_las_opciones_ordenadas_por_precio(self):
        caro = Shipping.objects.create(
            name='Envio expreso', time_to_delivery='24 h',
            description='Despacho al dia siguiente.', price=7900,
        )
        gratis = Shipping.objects.create(
            name='Retiro en taller', time_to_delivery='Mismo dia',
            description='Retiro coordinado.', price=0,
        )

        response = self.client.get('/api/shipp/get-shipping-options')

        self.assertEqual(
            [option['id'] for option in response.data['shipping_options']],
            [gratis.id, caro.id],
        )

    def test_la_opcion_puede_no_tener_foto(self):
        """"Retiro en taller" no tiene logo; el campo dejó de ser obligatorio."""
        opcion = Shipping.objects.create(
            name='Retiro en taller', time_to_delivery='Mismo dia',
            description='Retiro coordinado.', price=0,
        )

        self.assertFalse(opcion.photo)


class SeedShippingCommandTests(APITestCase):
    def test_seed_crea_las_opciones_base_y_es_idempotente(self):
        call_command('seed_shipping', stdout=StringIO())
        call_command('seed_shipping', stdout=StringIO())

        nombres = set(Shipping.objects.values_list('name', flat=True))
        self.assertIn('Starken - Por pagar', nombres)
        self.assertIn('Retiro en taller', nombres)
        self.assertEqual(Shipping.objects.count(), 2)

    def test_seed_no_pisa_lo_que_el_dueno_edito(self):
        Shipping.objects.create(
            name='Starken - Por pagar', time_to_delivery='1 dia',
            description='Editado a mano.', price=3500,
        )

        call_command('seed_shipping', stdout=StringIO())

        editada = Shipping.objects.get(name='Starken - Por pagar')
        self.assertEqual(editada.price, 3500)
        self.assertEqual(editada.description, 'Editado a mano.')

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

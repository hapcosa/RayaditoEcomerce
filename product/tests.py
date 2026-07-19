from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from metaproduct.models import Material
from product.models import Joyas

User = get_user_model()


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@rayadito.cl', password='Testpass123',
            first_name='Ana', last_name='Ríos',
        )
        cat = Category.objects.create(name='Anillos', ProductType='Joya')
        mat = Material.objects.create(name='Plata', cost=1000)
        self.product = Joyas.objects.create(
            name='Anillo', description='x', price=10000, compare_price=0,
            category=cat, material=mat, weight=Decimal('1.00'), photo='',
        )

    def _url(self, action):
        return f'/api/reviews/{action}/{self.product.id}'

    def test_list_empty_returns_200(self):
        res = self.client.get(self._url('get-reviews'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['reviews'], [])
        self.assertEqual(res.data['count'], 0)
        self.assertIsNone(res.data['average'])

    def test_create_requires_auth(self):
        res = self.client.post(self._url('create-review'),
                               {'rating': 4, 'comment': 'ok'}, format='json')
        self.assertIn(res.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_create_and_list(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(self._url('create-review'),
                               {'rating': '4.5', 'comment': 'bonito'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(res.data['reviews']), 1)

        res2 = self.client.get(self._url('get-reviews'))
        self.assertEqual(res2.data['count'], 1)
        self.assertEqual(str(res2.data['reviews'][0]['rating']), '4.5')

    def test_unique_per_user(self):
        self.client.force_authenticate(self.user)
        self.client.post(self._url('create-review'), {'rating': 4}, format='json')
        res = self.client.post(self._url('create-review'), {'rating': 3}, format='json')
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_invalid_rating(self):
        self.client.force_authenticate(self.user)
        too_high = self.client.post(self._url('create-review'),
                                    {'rating': 7}, format='json')
        self.assertEqual(too_high.status_code, 400)
        not_half = self.client.post(self._url('create-review'),
                                    {'rating': '2.3'}, format='json')
        self.assertEqual(not_half.status_code, 400)

    def test_update_and_delete(self):
        self.client.force_authenticate(self.user)
        self.client.post(self._url('create-review'),
                         {'rating': 4, 'comment': 'a'}, format='json')

        upd = self.client.put(self._url('update-review'),
                              {'rating': '5.0', 'comment': 'b'}, format='json')
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(str(upd.data['review']['rating']), '5.0')

        dele = self.client.delete(self._url('delete-review'))
        self.assertEqual(dele.status_code, 200)
        self.assertEqual(dele.data['reviews'], [])


class OpenAPISchemaTests(APITestCase):
    """El esquema OpenAPI y las docs se sirven sin errores (drf-spectacular)."""

    def test_schema_endpoint_ok(self):
        res = self.client.get('/api/schema')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_swagger_ui_ok(self):
        res = self.client.get('/api/docs')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_redoc_ok(self):
        res = self.client.get('/api/redoc')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

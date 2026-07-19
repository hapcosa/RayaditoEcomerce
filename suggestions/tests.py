from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from suggestions.models import Suggestion

User = get_user_model()


class SuggestionApiTests(APITestCase):
    def test_create_public_anonymous(self):
        res = self.client.post(
            '/api/suggestions/create',
            {'kind': 'sugerencia', 'message': 'Me encantó la tienda'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Suggestion.objects.count(), 1)
        s = Suggestion.objects.first()
        self.assertIsNone(s.user)
        self.assertEqual(s.status, Suggestion.Status.NEW)

    def test_create_links_authenticated_user(self):
        user = User.objects.create_user(
            email='ana@rayadito.cl', password='Testpass123',
            first_name='Ana', last_name='Ríos',
        )
        self.client.force_authenticate(user)
        res = self.client.post(
            '/api/suggestions/create',
            {'message': 'Agreguen más piedras azules'}, format='json',
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Suggestion.objects.first().user, user)

    def test_empty_message_rejected(self):
        res = self.client.post(
            '/api/suggestions/create', {'message': '  '}, format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_requires_admin(self):
        Suggestion.objects.create(message='hola')
        res = self.client.get('/api/suggestions/list')
        self.assertIn(res.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        user = User.objects.create_user(
            email='u@rayadito.cl', password='x', first_name='U', last_name='V')
        self.client.force_authenticate(user)
        res = self.client.get('/api/suggestions/list')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_admin_ok_and_filter(self):
        admin = User.objects.create_superuser(
            email='admin@rayadito.cl', password='x',
            first_name='Admin', last_name='Rayadito')
        Suggestion.objects.create(message='a', kind='reclamo')
        Suggestion.objects.create(message='b', kind='sugerencia')
        self.client.force_authenticate(admin)

        res = self.client.get('/api/suggestions/list')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)

        res2 = self.client.get('/api/suggestions/list?kind=reclamo')
        self.assertEqual(res2.data['count'], 1)

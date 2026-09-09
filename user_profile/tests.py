from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import UserProfile

User = get_user_model()

DIRECCION = {
    'label': 'Casa',
    'first_name': 'Ana',
    'last_name': 'Soto',
    'address_line_1': 'Av. Arturo Prat 123',
    'city': 'Ancud',
    'country_region': 'Los Lagos',
    'zipcode': '5710000',
    'phone': '+56 9 1234 5678',
}


class AddressBookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@example.cl', password='Rayadito2026', first_name='Ana', last_name='Soto',
        )
        self.otra = User.objects.create_user(
            email='otra@example.cl', password='Rayadito2026', first_name='Otra', last_name='Persona',
        )
        self.client.force_authenticate(user=self.user)

    def crear(self, **extra):
        return UserProfile.objects.create(user=self.user, **{**DIRECCION, **extra})

    def test_anonimo_no_ve_la_libreta(self):
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/profile/addresses/')

        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_crea_direccion(self):
        response = self.client.post('/api/profile/addresses/', DIRECCION, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'Casa')
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)

    def test_la_primera_direccion_queda_por_defecto(self):
        response = self.client.post('/api/profile/addresses/', DIRECCION, format='json')

        self.assertTrue(response.data['is_default'])

    def test_marcar_por_defecto_desmarca_la_anterior(self):
        primera = self.crear()
        segunda = self.crear(label='Taller', is_default=False)

        response = self.client.patch(
            f'/api/profile/addresses/{segunda.id}/', {'is_default': True}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        primera.refresh_from_db()
        segunda.refresh_from_db()
        self.assertFalse(primera.is_default)
        self.assertTrue(segunda.is_default)

    def test_no_se_queda_sin_direccion_por_defecto(self):
        unica = self.crear(is_default=True)

        self.client.patch(f'/api/profile/addresses/{unica.id}/', {'is_default': False}, format='json')

        unica.refresh_from_db()
        self.assertTrue(unica.is_default)

    def test_borrar_la_por_defecto_promueve_otra(self):
        default = self.crear(is_default=True)
        otra = self.crear(label='Taller', is_default=False)

        response = self.client.delete(f'/api/profile/addresses/{default.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        otra.refresh_from_db()
        self.assertTrue(otra.is_default)

    def test_solo_lista_las_propias(self):
        self.crear()
        UserProfile.objects.create(user=self.otra, **DIRECCION)

        response = self.client.get('/api/profile/addresses/')

        self.assertEqual(len(response.data), 1)

    def test_no_puede_leer_ni_editar_la_de_otro(self):
        ajena = UserProfile.objects.create(user=self.otra, **DIRECCION)

        detalle = self.client.get(f'/api/profile/addresses/{ajena.id}/')
        edicion = self.client.patch(
            f'/api/profile/addresses/{ajena.id}/', {'city': 'Castro'}, format='json',
        )

        self.assertEqual(detalle.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(edicion.status_code, status.HTTP_404_NOT_FOUND)
        ajena.refresh_from_db()
        self.assertEqual(ajena.city, 'Ancud')

    def test_edita_su_direccion(self):
        propia = self.crear()

        response = self.client.patch(
            f'/api/profile/addresses/{propia.id}/', {'city': 'Castro'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        propia.refresh_from_db()
        self.assertEqual(propia.city, 'Castro')

    def test_campos_obligatorios(self):
        response = self.client.post(
            '/api/profile/addresses/', {**DIRECCION, 'address_line_1': '   '}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('address_line_1', response.data)

    def test_la_region_es_texto_libre(self):
        """`country_region` guarda la región chilena, no un país de un choices."""
        response = self.client.post(
            '/api/profile/addresses/', {**DIRECCION, 'country_region': 'Los Lagos'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['country_region'], 'Los Lagos')

    def test_no_puede_crear_a_nombre_de_otro(self):
        response = self.client.post(
            '/api/profile/addresses/', {**DIRECCION, 'user': self.otra.id}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.get(id=response.data['id']).user, self.user)

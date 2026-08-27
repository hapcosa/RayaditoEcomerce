from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class CurrentUserStaffFlagTests(APITestCase):
    """El endpoint `/auth/users/me/` debe exponer `is_staff` (lo usa la app
    admin para verificar permisos), pero el registro público NUNCA debe
    permitir setear `is_staff`/`is_superuser` (escalada de privilegios)."""

    def test_me_exposes_is_staff_for_staff_user(self):
        staff = User.objects.create_user(
            email='staff@rayadito.cl',
            password='RayaditoTest2026',
            first_name='Staff',
            last_name='User',
            is_staff=True,
        )
        self.client.force_authenticate(user=staff)

        res = self.client.get('/auth/users/me/')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('is_staff', res.data)
        self.assertTrue(res.data['is_staff'])
        self.assertIn('is_superuser', res.data)
        self.assertFalse(res.data['is_superuser'])

    def test_me_reports_non_staff_as_false(self):
        user = User.objects.create_user(
            email='cliente@rayadito.cl',
            password='RayaditoTest2026',
            first_name='Cliente',
            last_name='Normal',
        )
        self.client.force_authenticate(user=user)

        res = self.client.get('/auth/users/me/')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_staff'])

    def test_public_registration_cannot_set_is_staff(self):
        res = self.client.post(
            '/auth/users/',
            {
                'email': 'atacante@rayadito.cl',
                'password': 'RayaditoTest2026',
                're_password': 'RayaditoTest2026',
                'first_name': 'Ata',
                'last_name': 'Cante',
                'is_staff': True,
                'is_superuser': True,
            },
            format='json',
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(email='atacante@rayadito.cl')
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)

"""Tests de la API admin de pedidos (/api/admin/orders/). Fase 5."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order

User = get_user_model()
S = Order.OrderStatus


class AdminOrderApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@rayadito.cl', password='Testpass123',
            first_name='Admin', last_name='Rayadito',
        )
        self.customer = User.objects.create_user(
            email='ana@rayadito.cl', password='Testpass123',
            first_name='Ana', last_name='Rios',
        )
        self.order = Order.objects.create(amount=29500, shipping_price=4500)

    def _status_url(self, order):
        return f'/api/admin/orders/{order.id}/status/'

    # --- permisos ---
    def test_list_requires_staff(self):
        self.client.force_authenticate(self.customer)
        res = self.client.get('/api/admin/orders/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_status_requires_staff(self):
        self.client.force_authenticate(self.customer)
        res = self.client.patch(self._status_url(self.order),
                                {'status': S.processed}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, S.not_processed)

    # --- listado ---
    def test_staff_lists_and_filters_orders(self):
        Order.objects.create(amount=10000, status=S.processed)
        self.client.force_authenticate(self.admin)
        res = self.client.get('/api/admin/orders/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)

        filtered = self.client.get('/api/admin/orders/', {'status': S.processed})
        self.assertEqual(filtered.data['count'], 1)
        self.assertEqual(filtered.data['results'][0]['status'], S.processed)

    # --- máquina de estados ---
    def test_valid_transition(self):
        self.client.force_authenticate(self.admin)
        res = self.client.patch(self._status_url(self.order),
                                {'status': S.processed}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, S.processed)

    def test_invalid_transition_is_400(self):
        # no procesado -> enviado no está permitido (falta pasar por procesado).
        self.client.force_authenticate(self.admin)
        res = self.client.patch(self._status_url(self.order),
                                {'status': S.shipping, 'deliveryNumber': 'STK-1'},
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('allowed_transitions', res.data)

    def test_shipping_requires_delivery_number(self):
        self.order.status = S.processed
        self.order.save(update_fields=['status'])
        self.client.force_authenticate(self.admin)
        res = self.client.patch(self._status_url(self.order),
                                {'status': S.shipping}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shipping_saves_tracking(self):
        self.order.status = S.processed
        self.order.save(update_fields=['status'])
        self.client.force_authenticate(self.admin)
        res = self.client.patch(self._status_url(self.order),
                                {'status': S.shipping, 'deliveryNumber': 'STK-999'},
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, S.shipping)
        self.assertEqual(self.order.deliveryNumber, 'STK-999')

    def test_invalid_status_value_is_400(self):
        self.client.force_authenticate(self.admin)
        res = self.client.patch(self._status_url(self.order),
                                {'status': 'entregado_ayer'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_terminal_state_cannot_transition(self):
        self.order.status = S.cancelled
        self.order.save(update_fields=['status'])
        self.client.force_authenticate(self.admin)
        res = self.client.patch(self._status_url(self.order),
                                {'status': S.processed}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

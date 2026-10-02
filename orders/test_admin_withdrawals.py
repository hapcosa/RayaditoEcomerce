"""API admin de solicitudes de retracto (app Expo)."""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, WithdrawalRequest

User = get_user_model()
W = WithdrawalRequest.Status


class AdminWithdrawalApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email='duena@rayadito.cl', password='Testpass123', first_name='D',
            last_name='R', is_staff=True)
        self.customer = User.objects.create_user(
            email='cliente@rayadito.cl', password='Testpass123', first_name='C', last_name='R')
        self.order = Order.objects.create(
            amount=29500, shipping_price=4500, full_name='Ines Perez',
            email='ines@correo.cl', paid_at=timezone.now(), transaction_id='987654')
        self.withdrawal = WithdrawalRequest.objects.create(
            order=self.order, code='RET-1-ABCD', email='ines@correo.cl', reason='No me quedó')
        self.client.force_authenticate(self.staff)

    def patch(self, data, pk=None):
        return self.client.patch(
            f'/api/admin/withdrawals/{pk or self.withdrawal.pk}/status/', data, format='json')

    def test_only_staff_can_see_them(self):
        self.client.force_authenticate(self.customer)

        self.assertEqual(self.client.get('/api/admin/withdrawals/').status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_list_includes_the_order_dates_to_judge_the_deadline(self):
        res = self.client.get('/api/admin/withdrawals/')

        item = res.data['results'][0] if isinstance(res.data, dict) else res.data[0]
        self.assertEqual(item['code'], 'RET-1-ABCD')
        self.assertEqual(item['order']['transaction_id'], '987654')
        self.assertIn('paid_at', item['order'])
        self.assertIn('shipped_at', item['order'])
        self.assertEqual(item['allowed_transitions'], ['accepted', 'rejected'])

    def test_open_filter(self):
        WithdrawalRequest.objects.create(
            order=self.order, code='RET-1-ZZZZ', email='ines@correo.cl', status=W.REFUNDED)

        res = self.client.get('/api/admin/withdrawals/', {'status': 'open'})

        data = res.data['results'] if isinstance(res.data, dict) else res.data
        self.assertEqual([w['code'] for w in data], ['RET-1-ABCD'])

    def test_accept_then_refund(self):
        accepted = self.patch({'status': 'accepted', 'staff_note': 'Dentro de plazo'})
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data['allowed_transitions'], ['refunded'])
        self.assertIsNone(accepted.data['resolved_at'])

        refunded = self.patch({'status': 'refunded'})

        self.withdrawal.refresh_from_db()
        self.assertEqual(refunded.status_code, status.HTTP_200_OK)
        self.assertEqual(self.withdrawal.status, W.REFUNDED)
        self.assertEqual(self.withdrawal.staff_note, 'Dentro de plazo')
        self.assertIsNotNone(self.withdrawal.resolved_at)

    def test_reject_requires_a_reason(self):
        res = self.patch({'status': 'rejected'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.patch({'status': 'rejected', 'staff_note': 'Fuera de plazo: recibido hace 40 días'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.withdrawal.refresh_from_db()
        self.assertIsNotNone(self.withdrawal.resolved_at)

    def test_invalid_transitions_are_refused(self):
        skip = self.patch({'status': 'refunded'})
        self.assertEqual(skip.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(skip.data['allowed_transitions'], ['accepted', 'rejected'])

        self.patch({'status': 'rejected', 'staff_note': 'x'})
        reopen = self.patch({'status': 'accepted'})
        self.assertEqual(reopen.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(self.patch({'status': 'nada'}).status_code,
                         status.HTTP_400_BAD_REQUEST)

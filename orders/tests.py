from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from metaproduct.models import Material
from orders.models import Order, OrderItem
from product.models import Joyas
from shipping.models import Shipping

User = get_user_model()


class OrderMoneyTests(TestCase):
    """Order.amount y OrderItem.price son enteros CLP."""

    def setUp(self):
        cat = Category.objects.create(name='Anillos', ProductType='Joya')
        mat = Material.objects.create(name='Plata', cost=15000)
        self.product = Joyas.objects.create(
            name='Anillo', description='x', price=25000, compare_price=0,
            category=cat, material=mat, weight=Decimal('1.00'), photo='',
        )

    def test_order_amount_is_integer(self):
        order = Order.objects.create(amount=37000, shipping_price=4500)
        order.refresh_from_db()
        self.assertIsInstance(order.amount, int)
        self.assertIsInstance(order.shipping_price, int)
        self.assertEqual(order.amount, 37000)
        self.assertEqual(order.shipping_price, 4500)

    def test_order_item_price_is_integer(self):
        order = Order.objects.create(amount=25000)
        item = OrderItem.objects.create(
            product=self.product, order=order, name='Anillo', price=25000,
        )
        item.refresh_from_db()
        self.assertIsInstance(item.price, int)
        self.assertEqual(item.price, 25000)
        self.assertEqual(item.count, 1)


class OrderDispatchApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@rayadito.cl',
            password='Testpass123',
            first_name='Admin',
            last_name='Rayadito',
        )
        self.user = User.objects.create_user(
            email='ana@rayadito.cl',
            password='Testpass123',
            first_name='Ana',
            last_name='Rios',
        )
        shipping = Shipping.objects.create(
            name='Envio manual Chiloe',
            time_to_delivery='2 a 4 dias habiles',
            description='Despacho manual con tracking.',
            price=4500,
            photo='',
        )
        self.order = Order.objects.create(
            amount=29500,
            shipping_price=4500,
            shipping_id=shipping,
        )

    def test_dispatch_requires_admin(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            f'/api/orders/dispatch/{self.order.id}',
            {'deliveryNumber': 'STK-123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.not_processed)
        self.assertIsNone(self.order.deliveryNumber)

    def test_dispatch_requires_delivery_number(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            f'/api/orders/dispatch/{self.order.id}',
            {'deliveryNumber': '  '},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_dispatch_saves_tracking_and_marks_shipped(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            f'/api/orders/dispatch/{self.order.id}',
            {'deliveryNumber': 'STK-123456'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.shipping)
        self.assertEqual(self.order.deliveryNumber, 'STK-123456')
        self.assertEqual(response.data['order']['deliveryNumber'], 'STK-123456')


class CustomerOrderApiTests(APITestCase):
    """`/api/orders/get-orders` y `/get-order/<id>` — vista del cliente.

    Cubre lo que el codigo legacy hacia mal: filtraba estados a mano (los
    pedidos `no procesado` y `cancelado` no aparecian nunca), reventaba con
    pedidos sin envio asociado y no exponia `deliveryNumber`.
    """

    def setUp(self):
        cat = Category.objects.create(name='Colgantes', ProductType='Joya')
        mat = Material.objects.create(name='Cobre', cost=8000)
        self.product = Joyas.objects.create(
            name='Colgante rayado', description='x', price=19000,
            compare_price=0, category=cat, material=mat,
            weight=Decimal('1.00'), photo='',
        )
        self.shipping = Shipping.objects.create(
            name='Starken por pagar',
            time_to_delivery='2 a 4 dias habiles',
            description='Retiro en sucursal.',
            price=4500,
            photo='',
        )
        self.user = User.objects.create_user(
            email='ana@rayadito.cl', password='Testpass123',
            first_name='Ana', last_name='Rios',
        )
        self.other = User.objects.create_user(
            email='otro@rayadito.cl', password='Testpass123',
            first_name='Otro', last_name='Cliente',
        )

    def _make_order(self, user, status_value, **extra):
        order = Order.objects.create(
            user=user, amount=23500, shipping_price=4500,
            status=status_value, shipping_id=self.shipping, **extra,
        )
        OrderItem.objects.create(
            product=self.product, order=order,
            name=self.product.name, price=19000, count=1,
        )
        return order

    def test_list_requires_authentication(self):
        response = self.client.get('/api/orders/get-orders')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_orders_in_every_status(self):
        for value in Order.OrderStatus.values:
            self._make_order(self.user, value, transaction_id=f'tx-{value}')
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/orders/get-orders')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned = {row['status'] for row in response.data['orders']}
        self.assertEqual(returned, set(Order.OrderStatus.values))

    def test_list_hides_orders_of_other_users(self):
        mine = self._make_order(self.user, Order.OrderStatus.processed, transaction_id='mia')
        self._make_order(self.other, Order.OrderStatus.processed, transaction_id='ajena')
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/orders/get-orders')

        self.assertEqual([row['id'] for row in response.data['orders']], [mine.id])

    def test_list_survives_order_without_shipping(self):
        """`shipping_id` es null=True; el codigo viejo hacia .id sobre None."""
        order = Order.objects.create(
            user=self.user, amount=19000, status=Order.OrderStatus.processed,
        )
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/orders/get-orders')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(r for r in response.data['orders'] if r['id'] == order.id)
        self.assertIsNone(row['shipping'])
        self.assertEqual(row['items_count'], 0)

    def test_detail_exposes_delivery_number_when_shipped(self):
        order = self._make_order(
            self.user, Order.OrderStatus.shipping,
            transaction_id='mp-9001', deliveryNumber='STK-778899',
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/orders/get-order/{order.transaction_id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order']['deliveryNumber'], 'STK-778899')
        self.assertEqual(response.data['order']['status'], Order.OrderStatus.shipping)
        self.assertEqual(response.data['order']['order_items'][0]['name'], 'Colgante rayado')

    def test_detail_delivery_number_is_null_before_dispatch(self):
        order = self._make_order(
            self.user, Order.OrderStatus.processed, transaction_id='mp-9002',
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/orders/get-order/{order.transaction_id}')

        self.assertIsNone(response.data['order']['deliveryNumber'])

    def test_detail_accepts_numeric_id_as_fallback(self):
        order = self._make_order(self.user, Order.OrderStatus.processed)
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/orders/get-order/{order.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order']['id'], order.id)

    def test_detail_of_other_user_returns_404(self):
        order = self._make_order(
            self.other, Order.OrderStatus.shipping,
            transaction_id='ajena-1', deliveryNumber='STK-000',
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/orders/get-order/{order.transaction_id}')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_amounts_are_integers_not_floats(self):
        self._make_order(self.user, Order.OrderStatus.processed, transaction_id='mp-clp')
        self.client.force_authenticate(self.user)

        row = self.client.get('/api/orders/get-orders').data['orders'][0]

        self.assertIsInstance(row['amount'], int)
        self.assertIsInstance(row['shipping_price'], int)

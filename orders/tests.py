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

from decimal import Decimal

from django.test import TestCase

from category.models import Category
from metaproduct.models import Material
from orders.models import Order, OrderItem
from product.models import Joyas


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

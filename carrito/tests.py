from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from carrito.models import Carrito, CarritoItem
from category.models import Category
from metaproduct.models import Material
from product.models import Joyas

User = get_user_model()


class CartMoneyTests(APITestCase):
    """El dinero viaja como entero CLP en toda la cadena carrito → total."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@rayadito.cl', password='x',
            first_name='Ana', last_name='Ríos',
        )
        # El manager crea el carrito al crear el usuario.
        self.cart = Carrito.objects.get(user=self.user)
        cat = Category.objects.create(name='Anillos', ProductType='Joya')
        self.material = Material.objects.create(name='Plata', cost=15000)  # entero CLP
        # compare_price=80000 era IMPOSIBLE con el DecimalField(6,2) anterior (máx 9999.99).
        self.p1 = Joyas.objects.create(
            name='Anillo', description='x', price=25000, compare_price=80000,
            category=cat, material=self.material, weight=Decimal('1.00'), photo='',
        )
        self.p2 = Joyas.objects.create(
            name='Aros', description='x', price=12000, compare_price=0,
            category=cat, material=self.material, weight=Decimal('1.00'), photo='',
        )

    def test_money_fields_are_integers(self):
        p = Joyas.objects.get(id=self.p1.id)
        self.assertIsInstance(p.price, int)
        self.assertEqual(p.price, 25000)
        self.assertEqual(p.compare_price, 80000)  # sin tope de 9999.99
        self.assertIsInstance(Material.objects.get(id=self.material.id).cost, int)

    def test_cart_total_is_integer_sum(self):
        CarritoItem.objects.create(carrito=self.cart, product=self.p1)
        CarritoItem.objects.create(carrito=self.cart, product=self.p2)
        self.client.force_authenticate(self.user)

        res = self.client.get('/api/cart/get-total')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cost'], 37000)
        self.assertEqual(res.data['total_compare_cost'], 80000)
        # Entero exacto, nunca float ni "37000.00".
        self.assertIsInstance(res.data['total_cost'], int)
        self.assertNotIsInstance(res.data['total_cost'], float)

    def test_empty_cart_total_is_zero_integer(self):
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/cart/get-total')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cost'], 0)
        self.assertIsInstance(res.data['total_cost'], int)

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from carrito.models import Carrito, CarritoItem
from category.models import Category
from metaproduct.models import Material
from product.models import Joyas, ProductVariant

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


class CartQuantityTests(APITestCase):
    """El carrito maneja cantidad (count) por item; total = precio x cantidad."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='ben@rayadito.cl', password='x',
            first_name='Ben', last_name='Soto',
        )
        self.cart = Carrito.objects.get(user=self.user)  # el manager lo crea
        cat = Category.objects.create(name='Anillos', ProductType='Joya')
        mat = Material.objects.create(name='Plata', cost=15000)
        self.p1 = Joyas.objects.create(
            name='Anillo', description='x', price=25000, compare_price=0,
            category=cat, material=mat, weight=Decimal('1.00'), photo='',
        )
        self.p2 = Joyas.objects.create(
            name='Aros', description='x', price=12000, compare_price=0,
            category=cat, material=mat, weight=Decimal('1.00'), photo='',
        )
        self.client.force_authenticate(self.user)

    def test_add_item_defaults_count_1(self):
        res = self.client.put('/api/cart/add-item',
                              {'product_id': self.p1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res.data['cart']), 1)
        self.assertEqual(res.data['cart'][0]['count'], 1)
        self.assertEqual(Carrito.objects.get(id=self.cart.id).total_items, 1)

    def test_add_same_product_twice_conflicts(self):
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')
        res = self.client.put('/api/cart/add-item',
                              {'product_id': self.p1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_update_item_count_updates_total_items(self):
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')
        res = self.client.put('/api/cart/update-item',
                              {'product_id': self.p1.id, 'count': 3}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['cart'][0]['count'], 3)
        self.assertEqual(Carrito.objects.get(id=self.cart.id).total_items, 3)

    def test_update_item_count_zero_rejected(self):
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')
        res = self.client.put('/api/cart/update-item',
                              {'product_id': self.p1.id, 'count': 0}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_total_is_price_times_count(self):
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')
        self.client.put('/api/cart/add-item', {'product_id': self.p2.id}, format='json')
        self.client.put('/api/cart/update-item',
                        {'product_id': self.p1.id, 'count': 2}, format='json')

        res = self.client.get('/api/cart/get-total')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 25000*2 + 12000*1 = 62000
        self.assertEqual(res.data['total_cost'], 62000)
        self.assertIsInstance(res.data['total_cost'], int)

    def test_total_items_is_sum_of_counts(self):
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')
        self.client.put('/api/cart/add-item', {'product_id': self.p2.id}, format='json')
        self.client.put('/api/cart/update-item',
                        {'product_id': self.p1.id, 'count': 4}, format='json')
        res = self.client.get('/api/cart/get-item-total')
        self.assertEqual(res.data['total_items'], 5)  # 4 + 1

    def test_remove_item_recomputes_total(self):
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')
        self.client.put('/api/cart/update-item',
                        {'product_id': self.p1.id, 'count': 3}, format='json')
        self.client.put('/api/cart/add-item', {'product_id': self.p2.id}, format='json')

        res = self.client.delete('/api/cart/remove-item',
                                 {'product_id': self.p1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['cart']), 1)
        self.assertEqual(Carrito.objects.get(id=self.cart.id).total_items, 1)

    def test_update_item_not_in_cart_404(self):
        res = self.client.put('/api/cart/update-item',
                              {'product_id': self.p1.id, 'count': 2}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_item_count_respects_variant_stock(self):
        ProductVariant.objects.create(product=self.p1, sku='ANI-1', stock=2)
        self.client.put('/api/cart/add-item', {'product_id': self.p1.id}, format='json')

        too_many = self.client.put('/api/cart/update-item',
                                   {'product_id': self.p1.id, 'count': 3}, format='json')
        self.assertEqual(too_many.status_code, status.HTTP_200_OK)
        self.assertEqual(too_many.data['error'], 'Not enough of this item in stock')

        ok = self.client.put('/api/cart/update-item',
                             {'product_id': self.p1.id, 'count': 2}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertEqual(ok.data['cart'][0]['count'], 2)

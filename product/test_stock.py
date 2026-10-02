"""Inventario: `Product.stock` entero, `sold` derivado, variantes para los forks.

Cubre la cadena completa donde el stock decide algo: catalogo, carrito,
checkout, webhook de pago y app admin (incluido el APK viejo que manda `sold`).
"""
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from carrito.models import Carrito, CarritoItem
from category.models import Category
from orders.models import Order, OrderItem
from payment import services
from payment.models import Payments
from payment.tests import FakeMercadoPagoSDK
from product.models import Product, ProductVariant
from shipping.models import Shipping

User = get_user_model()


def make_product(category, name='Anillo', **extra):
    return Product.objects.create(
        name=name, description='x', price=25000, compare_price=0, category=category,
        product_type=Product.ProductType.JOYA, photo='', **extra)


class StockModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')

    def test_new_products_are_a_single_piece(self):
        product = make_product(self.category)

        self.assertEqual(product.stock, 1)
        self.assertEqual(product.available_stock, 1)
        self.assertFalse(product.sold)

    def test_sold_is_derived_from_stock(self):
        product = make_product(self.category, stock=0)

        self.assertTrue(product.sold)

    def test_active_variants_override_product_stock(self):
        product = make_product(self.category, stock=0)
        ProductVariant.objects.create(product=product, sku='A', stock=2)
        ProductVariant.objects.create(product=product, sku='B', stock=5, is_active=False)

        self.assertEqual(product.available_stock, 2)
        self.assertFalse(product.sold)

    def test_querysets_match_the_property(self):
        disponible = make_product(self.category, name='Disponible', stock=3)
        agotada = make_product(self.category, name='Agotada', stock=0)
        con_variantes = make_product(self.category, name='Variantes', stock=0)
        ProductVariant.objects.create(product=con_variantes, stock=1)
        variantes_agotadas = make_product(self.category, name='Variantes agotadas', stock=5)
        ProductVariant.objects.create(product=variantes_agotadas, stock=0)
        solo_inactivas = make_product(self.category, name='Solo inactivas', stock=2)
        ProductVariant.objects.create(product=solo_inactivas, stock=0, is_active=False)

        available = set(Product.objects.available().values_list('name', flat=True))
        sold_out = set(Product.objects.sold_out().values_list('name', flat=True))

        self.assertEqual(available, {'Disponible', 'Variantes', 'Solo inactivas'})
        self.assertEqual(sold_out, {'Agotada', 'Variantes agotadas'})
        for product in (disponible, agotada, con_variantes, variantes_agotadas, solo_inactivas):
            self.assertEqual(product.name in sold_out, product.sold, product.name)

    def test_available_does_not_duplicate_rows_with_several_variants(self):
        product = make_product(self.category, stock=0)
        ProductVariant.objects.create(product=product, stock=1)
        ProductVariant.objects.create(product=product, stock=1)

        self.assertEqual(Product.objects.available().count(), 1)


class StockServiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')

    def test_has_stock_respects_quantity(self):
        product = make_product(self.category, stock=3)

        self.assertTrue(services.has_stock(product, 3))
        self.assertFalse(services.has_stock(product, 4))

    def test_deduct_lowers_product_stock(self):
        product = make_product(self.category, stock=3)

        services.deduct_product_stock(product, 2)

        product.refresh_from_db()
        self.assertEqual(product.stock, 1)

    def test_deduct_never_goes_below_zero(self):
        # Dos pagos aprobados por la ultima pieza: queda agotada, no en -1.
        product = make_product(self.category, stock=1)

        services.deduct_product_stock(product, 1)
        services.deduct_product_stock(product, 1)

        product.refresh_from_db()
        self.assertEqual(product.stock, 0)
        self.assertTrue(product.sold)

    def test_deduct_uses_variants_when_they_exist(self):
        product = make_product(self.category, stock=7)
        first = ProductVariant.objects.create(product=product, stock=1)
        second = ProductVariant.objects.create(product=product, stock=4)

        services.deduct_product_stock(product, 3)

        first.refresh_from_db()
        second.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual((first.stock, second.stock), (0, 2))
        self.assertEqual(product.stock, 7)


class StockMigrationTests(TransactionTestCase):
    """`sold=True` pasa a stock 0 y `sold=False` a 1, y la vuelta atras deshace."""

    before = [('product', '0013_drop_product_subclasses')]
    after = [('product', '0014_product_stock')]

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(target)
        return executor.loader.project_state(target).apps

    def tearDown(self):
        self.migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_sold_flag_becomes_stock(self):
        apps = self.migrate(self.before)
        OldCategory = apps.get_model('category', 'Category')
        OldProduct = apps.get_model('product', 'Product')
        category = OldCategory.objects.create(name='Anillos', ProductType='Joya')
        common = dict(description='x', price=1000, compare_price=0, category=category,
                      product_type='joya', photo='')
        OldProduct.objects.create(name='Vendida', slug='vendida', sold=True, **common)
        OldProduct.objects.create(name='Disponible', slug='disponible', sold=False, **common)

        apps = self.migrate(self.after)
        NewProduct = apps.get_model('product', 'Product')
        self.assertEqual(NewProduct.objects.get(name='Vendida').stock, 0)
        self.assertEqual(NewProduct.objects.get(name='Disponible').stock, 1)

        apps = self.migrate(self.before)
        OldProduct = apps.get_model('product', 'Product')
        self.assertTrue(OldProduct.objects.get(name='Vendida').sold)
        self.assertFalse(OldProduct.objects.get(name='Disponible').sold)


class CatalogAndCartTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.user = User.objects.create_user(
            email='ana@rayadito.cl', password='Testpass123', first_name='Ana', last_name='R')
        self.client.force_authenticate(self.user)

    def test_public_api_exposes_derived_sold(self):
        product = make_product(self.category, stock=0)

        res = self.client.get(f'/api/products/{product.slug}')

        self.assertTrue(res.data['product']['sold'])
        self.assertEqual(res.data['product']['available_stock'], 0)

    def test_sold_out_products_cannot_be_added_to_the_cart(self):
        product = make_product(self.category, stock=0)

        self.client.put('/api/cart/add-item', {'product_id': product.id}, format='json')

        self.assertFalse(CarritoItem.objects.exists())

    def test_cart_count_is_limited_by_stock(self):
        product = make_product(self.category, stock=2)
        self.client.put('/api/cart/add-item', {'product_id': product.id}, format='json')

        ok = self.client.put('/api/cart/update-item',
                             {'product_id': product.id, 'count': 2}, format='json')
        # Contrato existente del carrito: 200 con `error`, la web lo muestra.
        too_many = self.client.put('/api/cart/update-item',
                                   {'product_id': product.id, 'count': 3}, format='json')

        self.assertNotIn('error', ok.data)
        self.assertEqual(too_many.data['error'], 'Not enough of this item in stock')
        self.assertEqual(CarritoItem.objects.get().count, 2)


@mock.patch.dict(os.environ, {'MERCADOPAGO_ACCESS_TOKEN': 'test-token'}, clear=False)
class CheckoutAndWebhookTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = make_product(self.category, stock=2)
        self.shipping = Shipping.objects.create(
            name='Retiro', time_to_delivery='1 día', description='-', price=0)

    def pay_as_guest(self, count):
        sdk = FakeMercadoPagoSDK(preference_response={'id': 'pref'})
        with mock.patch('payment.services.mercadopago_sdk', return_value=sdk):
            return self.client.post('/api/payment/make-payment', {
                'shipping_id': self.shipping.id, 'email': 'a@b.cl',
                'first_name': 'Ines', 'last_name': 'Perez', 'address_line_1': 'Calle 1',
                'city': 'Castro', 'state_province_region': 'Los Lagos',
                'postal_zip_code': '', 'telephone_number': '912345678',
                'items': [{'product': {'id': self.product.id}, 'count': count}],
            }, format='json')

    def test_checkout_refuses_more_than_the_stock(self):
        res = self.pay_as_guest(3)

        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(Order.objects.exists())

    def test_checkout_accepts_up_to_the_stock(self):
        self.assertEqual(self.pay_as_guest(2).status_code, status.HTTP_200_OK)

    def approve(self, order, payment_id):
        sdk = FakeMercadoPagoSDK(payment_response={
            'id': payment_id, 'external_reference': str(order.id), 'status': 'approved',
            'status_detail': 'accredited', 'payment_method_id': 'visa',
            'payment_type_id': 'credit_card', 'installments': 1,
        })
        with mock.patch('payment.services.mercadopago_sdk', return_value=sdk):
            return self.client.post('/api/payment/webhook',
                                    {'type': 'payment', 'data': {'id': str(payment_id)}},
                                    format='json')

    def order_for(self, count):
        order = Order.objects.create(amount=25000 * count, shipping_id=self.shipping)
        OrderItem.objects.create(order=order, product=self.product, name='Anillo',
                                 price=25000, count=count)
        return order

    def test_approved_payment_deducts_stock_once(self):
        order = self.order_for(1)

        self.approve(order, 111)
        self.approve(order, 111)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertTrue(Payments.objects.get(order=order).stock_deducted)

    def test_last_unit_sold_hides_the_product(self):
        self.approve(self.order_for(2), 222)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
        self.assertTrue(self.product.sold)
        self.assertFalse(Product.objects.available().filter(pk=self.product.pk).exists())


class AdminApiStockTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.product = make_product(self.category, stock=1)
        self.staff = User.objects.create_user(
            email='duena@rayadito.cl', password='Testpass123', first_name='D',
            last_name='R', is_staff=True)
        self.client.force_authenticate(self.staff)
        self.url = f'/api/admin/products/{self.product.id}/'

    def patch(self, data, fmt='json'):
        res = self.client.patch(self.url, data, format=fmt)
        self.product.refresh_from_db()
        return res

    def test_stock_is_editable(self):
        res = self.patch({'stock': 4})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.product.stock, 4)
        self.assertEqual(res.data['available_stock'], 4)
        self.assertFalse(res.data['sold'])

    def test_negative_stock_is_rejected(self):
        res = self.patch({'stock': -1})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.product.stock, 1)

    def test_old_apk_sold_switch_still_works(self):
        # El APK instalado manda multipart con sold='true' / 'false'.
        res = self.patch({'sold': 'true'}, fmt='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.product.stock, 0)
        self.assertTrue(res.data['sold'])

        self.patch({'sold': 'false'}, fmt='multipart')
        self.assertEqual(self.product.stock, 1)

    def test_unsold_switch_keeps_a_higher_stock(self):
        self.patch({'stock': 3})

        self.patch({'sold': False})

        self.assertEqual(self.product.stock, 3)

    def test_explicit_stock_wins_over_sold(self):
        self.patch({'stock': 2, 'sold': True})

        self.assertEqual(self.product.stock, 2)

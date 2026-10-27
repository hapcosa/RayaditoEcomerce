"""`seed_demo`: carga el catálogo demo sobre el modelo de atributos."""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from core.store import validate_store

from category.models import Category
from product.models import Product, ProductAttributeValue
from shipping.models import Shipping


class SeedDemoTests(TestCase):
    def seed(self):
        call_command('seed_demo', stdout=StringIO())

    def test_creates_one_product_per_public_catalog(self):
        self.seed()

        anillo = Product.objects.get(name='Anillo de plata con ágata')
        agata = Product.objects.get(name='Ágata lapidada')
        self.assertEqual(anillo.product_type, 'joya')
        self.assertEqual(agata.product_type, 'piedra')
        self.assertEqual(anillo.price, 25000)
        self.assertEqual(Shipping.objects.count(), 2)

    def test_stores_details_as_attribute_values(self):
        self.seed()

        valores = dict(
            ProductAttributeValue.objects
            .filter(product__name='Ágata lapidada')
            .values_list('attribute_value__attribute__slug', 'attribute_value__value')
        )
        self.assertEqual(valores['nombre-piedra'], 'Ágata de Chiloé')
        self.assertEqual(valores['largo'], '3,5')
        joyas = Category.objects.get(name='Joyas')
        self.assertIn('material', joyas.attributes.values_list('slug', flat=True))

    def test_is_idempotent(self):
        self.seed()
        self.seed()

        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(
            ProductAttributeValue.objects.filter(product__name='Ágata lapidada').count(), 6,
        )


TEXTIL = validate_store({
    'slug': 'textil', 'name': 'Tienda Textil', 'short_name': 'Textil',
    'description': 'Ropa tejida a mano.', 'domain': 'textil.test', 'rubro': 'textil',
    'catalogs': [{
        'slug': 'ropa', 'path': 'ropa', 'label': 'Ropa', 'singular': 'Prenda',
        'category_type': 'Ropa',
    }],
})


@override_settings(STORE=TEXTIL)
class SeedDemoTextilTests(TestCase):
    def test_uses_the_store_rubro_by_default(self):
        call_command('seed_demo', stdout=StringIO())

        chaleco = Product.objects.get(name='Chaleco de lana de oveja')
        self.assertEqual(chaleco.product_type, 'ropa')
        self.assertEqual(chaleco.category.ProductType, 'Ropa')
        valores = dict(
            ProductAttributeValue.objects.filter(product=chaleco)
            .values_list('attribute_value__attribute__slug', 'attribute_value__value')
        )
        self.assertEqual(valores['talla'], 'M')
        self.assertFalse(Product.objects.filter(product_type='joya').exists())

    def test_refuses_a_rubro_whose_catalogs_the_store_lacks(self):
        with self.assertRaisesMessage(CommandError, 'joya, piedra'):
            call_command('seed_demo', '--rubro', 'joyeria', stdout=StringIO())

        self.assertEqual(Product.objects.count(), 0)


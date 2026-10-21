"""`seed_demo`: carga el catálogo demo sobre el modelo de atributos."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

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
        self.assertEqual(anillo.product_type, Product.ProductType.JOYA)
        self.assertEqual(agata.product_type, Product.ProductType.PIEDRA)
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

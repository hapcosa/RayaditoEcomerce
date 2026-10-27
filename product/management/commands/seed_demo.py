"""Carga datos demo mínimos para desarrollo (idempotente).

    python manage.py seed_demo                 # rubro de store.json ("rubro")
    python manage.py seed_demo --rubro textil

Crea los atributos que falten, categorías con sus atributos, un par de
productos y dos opciones de envío, según el rubro (ver product/seeds.py). Útil
para levantar la tienda con catálogo no vacío tras un `migrate` en una base
limpia. NO usar en producción.

Material, talla, medidas, etc. van como atributos del producto
(`ProductAttributeValue`), igual que los carga la app admin.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from category.models import Category, CategoryAttribute
from core import store
from product.models import Attribute, AttributeValue, Product, ProductAttributeValue
from product.seeds import SEEDS, SHIPPING
from shipping.models import Shipping


class Command(BaseCommand):
    help = "Carga datos demo mínimos para desarrollo (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--rubro', choices=sorted(SEEDS),
            help='Set de datos demo. Por defecto, el "rubro" de store.json (o joyeria).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rubro = options['rubro'] or settings.STORE.get('rubro') or 'joyeria'
        if rubro not in SEEDS:
            raise CommandError(f'Rubro "{rubro}" sin datos demo; opciones: {", ".join(sorted(SEEDS))}')
        seed = SEEDS[rubro]
        self._check_catalogs(rubro, seed)

        atributos = self._atributos(seed['attributes'])
        categorias = self._categorias(seed['categories'], atributos)
        for data in seed['products']:
            producto, _ = Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    'product_type': data['catalog'],
                    'description': data['description'],
                    'price': data['price'],
                    'category': categorias[data['category']],
                    'photo': '',
                },
            )
            self._enganchar_producto(producto, atributos, data['attributes'])

        for data in SHIPPING:
            Shipping.objects.get_or_create(
                name=data['name'],
                defaults={
                    'time_to_delivery': data['time_to_delivery'],
                    'description': data['description'],
                    'photo': '',
                },
            )

        self.stdout.write(self.style.SUCCESS(f'Datos demo cargados ({rubro}).'))

    def _check_catalogs(self, rubro, seed):
        """Los productos tienen que caer en catálogos que esta tienda publica."""
        faltan = sorted({p['catalog'] for p in seed['products']
                         if store.catalog_by_slug(p['catalog']) is None})
        if faltan:
            raise CommandError(
                f'Los datos demo "{rubro}" usan catálogos que store.json no tiene: '
                f'{", ".join(faltan)}. Agrégalos a "catalogs" o usa otro --rubro.'
            )

    def _atributos(self, specs):
        atributos = {}
        for orden, spec in enumerate(specs):
            atributos[spec['slug']], _ = Attribute.objects.get_or_create(
                slug=spec['slug'],
                defaults={
                    'name': spec['name'],
                    'kind': spec['kind'],
                    'unit': spec.get('unit', ''),
                    'sort_order': orden,
                },
            )
        return atributos

    def _categorias(self, specs, atributos):
        categorias = {}
        for spec in specs:
            parent = categorias.get(spec.get('parent'))
            categoria, _ = Category.objects.get_or_create(
                name=spec['name'],
                defaults={'ProductType': spec['category_type'], 'parent': parent},
            )
            categorias[spec['name']] = categoria
            for orden, slug in enumerate(spec.get('attributes', [])):
                CategoryAttribute.objects.get_or_create(
                    category=categoria, attribute=atributos[slug],
                    defaults={'sort_order': orden},
                )
        return categorias

    def _enganchar_producto(self, producto, atributos, valores):
        for slug, (texto, numero) in valores.items():
            valor, _ = AttributeValue.objects.get_or_create(
                attribute=atributos[slug], value=texto,
                defaults={'numeric_value': numero},
            )
            ProductAttributeValue.objects.get_or_create(
                product=producto, attribute_value=valor,
            )

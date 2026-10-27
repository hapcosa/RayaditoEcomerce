"""Carga datos demo mínimos para desarrollo (idempotente).

    python manage.py seed_demo

Crea categorías (joya/piedra) con sus atributos, una joya, una piedra y dos
opciones de envío. Útil para levantar la tienda con catálogo no vacío tras un
`migrate` en una base limpia. NO usar en producción.

Material, peso, tipo de piedra y medidas van como atributos del producto
(`ProductAttributeValue`), igual que los carga la app admin. Los atributos
vienen sembrados por `product.0009_generic_product_variants`.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from category.models import Category, CategoryAttribute
from product.models import Attribute, AttributeValue, Product, ProductAttributeValue
from shipping.models import Shipping

# slug del atributo -> (texto es-CL, valor numérico o None)
ATRIBUTOS_JOYA = {
    'material': ('Plata 950', None),
    'peso': ('12,5', Decimal('12.5')),
}
ATRIBUTOS_PIEDRA = {
    'nombre-piedra': ('Ágata de Chiloé', None),
    'dureza-mohs': ('7', Decimal('7')),
    'origen': ('Volcanico', None),
    'largo': ('3,5', Decimal('3.5')),
    'ancho': ('2', Decimal('2')),
    'alto': ('1,2', Decimal('1.2')),
}


class Command(BaseCommand):
    help = "Carga datos demo mínimos para desarrollo (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        atributos = Attribute.objects.in_bulk(
            [*ATRIBUTOS_JOYA, *ATRIBUTOS_PIEDRA], field_name='slug',
        )

        # Categorías (jerárquicas) para joyas y piedras. Los atributos se
        # declaran en la raíz y las hijas los heredan.
        joyas_root, _ = Category.objects.get_or_create(
            name="Joyas", defaults={"ProductType": "Joya"}
        )
        anillos, _ = Category.objects.get_or_create(
            name="Anillos", defaults={"ProductType": "Joya", "parent": joyas_root}
        )
        piedras_root, _ = Category.objects.get_or_create(
            name="Piedras", defaults={"ProductType": "Piedra"}
        )
        agatas, _ = Category.objects.get_or_create(
            name="Ágatas", defaults={"ProductType": "Piedra", "parent": piedras_root}
        )
        self._enganchar_categoria(joyas_root, atributos, ATRIBUTOS_JOYA)
        self._enganchar_categoria(piedras_root, atributos, ATRIBUTOS_PIEDRA)

        # Productos.
        anillo, _ = Product.objects.get_or_create(
            name="Anillo de plata con ágata",
            defaults={
                "product_type": 'joya',
                "description": "Anillo artesanal de plata 950 con ágata de Chiloé.",
                "price": 25000,
                "category": anillos,
                "photo": "",
            },
        )
        self._enganchar_producto(anillo, atributos, ATRIBUTOS_JOYA)

        agata, _ = Product.objects.get_or_create(
            name="Ágata lapidada",
            defaults={
                "product_type": 'piedra',
                "description": "Ágata local lapidada a mano.",
                "price": 12000,
                "category": agatas,
                "photo": "",
            },
        )
        self._enganchar_producto(agata, atributos, ATRIBUTOS_PIEDRA)

        # Opciones de envío.
        Shipping.objects.get_or_create(
            name="Starken - Por pagar",
            defaults={
                "time_to_delivery": "2 a 5 días hábiles",
                "description": "Envío a sucursal Starken, pago en destino.",
                "photo": "",
            },
        )
        Shipping.objects.get_or_create(
            name="Retiro en taller",
            defaults={
                "time_to_delivery": "Coordinar",
                "description": "Retiro en el taller en Chiloé.",
                "photo": "",
            },
        )

        faltantes = sorted({*ATRIBUTOS_JOYA, *ATRIBUTOS_PIEDRA} - set(atributos))
        if faltantes:
            self.stdout.write(self.style.WARNING(
                f"Atributos no sembrados, se omitieron: {', '.join(faltantes)}"
            ))
        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))

    def _enganchar_categoria(self, categoria, atributos, valores):
        for orden, slug in enumerate(valores):
            if slug in atributos:
                CategoryAttribute.objects.get_or_create(
                    category=categoria, attribute=atributos[slug],
                    defaults={"sort_order": orden},
                )

    def _enganchar_producto(self, producto, atributos, valores):
        for slug, (texto, numero) in valores.items():
            if slug not in atributos:
                continue
            valor, _ = AttributeValue.objects.get_or_create(
                attribute=atributos[slug], value=texto,
                defaults={"numeric_value": numero},
            )
            ProductAttributeValue.objects.get_or_create(
                product=producto, attribute_value=valor,
            )

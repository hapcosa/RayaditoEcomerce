"""Carga datos demo mínimos para desarrollo (idempotente).

    python manage.py seed_demo

Crea categorías (joya/piedra), un material, un tipo de piedra, una joya, una
piedra y dos opciones de envío. Útil para levantar la tienda con catálogo no
vacío tras un `migrate` en una base limpia. NO usar en producción.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from category.models import Category
from metaproduct.models import Material, NombrePiedra
from product.models import Joyas, Piedras
from shipping.models import Shipping


class Command(BaseCommand):
    help = "Carga datos demo mínimos para desarrollo (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        # Categorías (jerárquicas) para joyas y piedras.
        joyas_root, _ = Category.objects.get_or_create(
            name="Joyas", defaults={"ProductType": "Joya"}
        )
        Category.objects.get_or_create(
            name="Anillos", defaults={"ProductType": "Joya", "parent": joyas_root}
        )
        piedras_root, _ = Category.objects.get_or_create(
            name="Piedras", defaults={"ProductType": "Piedra"}
        )
        Category.objects.get_or_create(
            name="Ágatas", defaults={"ProductType": "Piedra", "parent": piedras_root}
        )

        # Metaproductos.
        plata, _ = Material.objects.get_or_create(name="Plata 950", defaults={"cost": 15000})
        agata, _ = NombrePiedra.objects.get_or_create(
            name="Ágata de Chiloé", defaults={"mohs": "7.000", "origen": "Volcanico"}
        )

        # Productos. compare_price=0 respeta el límite del campo actual
        # (max_digits=6); la normalización a CLP entero es parte de la Fase 1.
        anillos = Category.objects.get(name="Anillos")
        Joyas.objects.get_or_create(
            name="Anillo de plata con ágata",
            defaults={
                "description": "Anillo artesanal de plata 950 con ágata de Chiloé.",
                "price": 25000,
                "compare_price": 0,
                "category": anillos,
                "material": plata,
                "weight": "12.50",
                "photo": "",
            },
        )
        agatas = Category.objects.get(name="Ágatas")
        Piedras.objects.get_or_create(
            name="Ágata lapidada",
            defaults={
                "description": "Ágata local lapidada a mano.",
                "price": 12000,
                "compare_price": 0,
                "category": agatas,
                "nombrePiedra": agata,
                "large": "3.50",
                "width": "2.00",
                "height": "1.20",
                "photo": "",
            },
        )

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

        self.stdout.write(self.style.SUCCESS("Datos demo cargados."))

from django.core.management.base import BaseCommand

from shipping.models import Shipping

# Opciones mínimas para que el checkout no quede sin métodos de envío. Precio en
# entero CLP; `0` = lo paga quien recibe (Starken por pagar) o no hay costo
# (retiro). El dueño ajusta nombre, plazo y precio desde /admin/.
OPCIONES = [
    {
        'name': 'Starken - Por pagar',
        'time_to_delivery': '3 a 5 días hábiles',
        'description': (
            'Despacho por Starken a la sucursal más cercana. El flete se paga '
            'al retirar el paquete.'
        ),
        'price': 0,
    },
    {
        'name': 'Retiro en taller',
        'time_to_delivery': 'Coordinado, mismo día',
        'description': 'Retiro sin costo en el taller, coordinando día y hora por WhatsApp.',
        'price': 0,
    },
]


class Command(BaseCommand):
    help = 'Crea las opciones de envío base si todavía no existen (idempotente).'

    def handle(self, *args, **options):
        for datos in OPCIONES:
            _, creada = Shipping.objects.get_or_create(
                name=datos['name'], defaults=datos,
            )
            estado = 'creada' if creada else 'ya existía'
            self.stdout.write(f"{datos['name']}: {estado}")
        self.stdout.write(self.style.SUCCESS(
            f'Opciones de envío disponibles: {Shipping.objects.count()}'
        ))

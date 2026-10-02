"""Emite en Starken la orden de flete de un pedido pagado.

Se corre a mano, pedido por pedido, cuando el paquete esta listo: la OF trae
una etiqueta que hay que imprimir, asi que emitirla sola al pagar no ahorra
trabajo y deja OF huerfanas si el pedido se cancela.
"""
from django.core.management.base import BaseCommand, CommandError

from orders.models import Order
from shipping import starken
from shipping.shipments import create_shipment


class Command(BaseCommand):
    help = 'Create the Starken freight order (OF) for a paid order.'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int)
        parser.add_argument('--agencia', help='Destination agency code (pickup at agency).')
        parser.add_argument('--boleta', help='Boleta number; required over $50.000 declared.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Print the payload (without the password) and stop.')

    def handle(self, *args, order_id, agencia, boleta, dry_run, **options):
        if not starken.is_enabled():
            raise CommandError('Starken no esta activado (STARKEN_ENABLED).')
        try:
            order = Order.objects.select_related('shipping_id', 'user').get(pk=order_id)
        except Order.DoesNotExist:
            raise CommandError(f'No existe el pedido {order_id}.') from None
        try:
            if dry_run:
                payload = starken.emission_payload(
                    order, agency_code=agencia, document_number=boleta)
                payload['claveUsuarioEmisor'] = '***'
                for key, value in payload.items():
                    self.stdout.write(f'{key}: {value}')
                return
            shipment = create_shipment(order, agency_code=agencia, document_number=boleta)
        except starken.StarkenError as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS(
            f'Pedido {order.pk}: OF {shipment.tracking_number}. Imprime la etiqueta '
            'desde Emision Web de Starken.'))

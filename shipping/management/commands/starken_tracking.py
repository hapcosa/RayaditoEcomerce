"""Actualiza el estado de los pedidos despachados por Starken.

Pensado para un timer de systemd (ver docs/STARKEN.md). Solo consulta los
pedidos "enviado" cuyo envio no llego a un estado terminal.
"""
from django.core.management.base import BaseCommand

from shipping import starken
from shipping.shipments import sync_tracking


class Command(BaseCommand):
    help = 'Refresh Starken tracking status for shipped orders.'

    def handle(self, *args, **options):
        if not starken.is_enabled():
            self.stdout.write('Starken no esta activado; nada que hacer.')
            return
        ok, failed = sync_tracking()
        self.stdout.write(f'{ok} envio(s) actualizados, {failed} con error.')
        if failed:
            self.stderr.write('Revisa last_error en /admin/shipping/shipment/.')

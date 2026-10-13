"""Reintenta con el proveedor los documentos tributarios que fallaron.

Solo hace algo con BILLING_MODE='provider'. Las boletas deben llegar al SII
dentro de la hora siguiente a la venta, asi que con proveedor conviene correrlo
cada 10 minutos desde un timer de systemd (ver docs/SII.md).
"""
from django.core.management.base import BaseCommand

from billing.services import mode, retry_failed


class Command(BaseCommand):
    help = 'Retry issuing the failed tax documents with the configured provider.'

    def handle(self, *args, **options):
        if mode() != 'provider':
            self.stdout.write(f"BILLING_MODE is '{mode()}': nothing to issue.")
            return
        issued, attempted = retry_failed()
        self.stdout.write(f'Issued {issued} of {attempted} pending document(s).')

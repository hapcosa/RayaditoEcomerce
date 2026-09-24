"""Aviso de plazo de despacho por vencer.

Pensado para correr cada hora desde un timer de systemd (ver docs/DEPLOY.md).
El proyecto no tiene Celery a proposito: un comando idempotente que se puede
correr a mano es mas facil de depurar que una cola.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.services import notify_pending_dispatch, orders_to_warn


class Command(BaseCommand):
    help = 'Warn the owner about paid orders whose dispatch deadline is near.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List the orders that would be warned about, without notifying.',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        pending = list(orders_to_warn(now))
        if not pending:
            self.stdout.write('No orders are close to their dispatch deadline.')
            return

        warned = 0
        for order in pending:
            if options['dry_run']:
                self.stdout.write(f'Order {order.id}: paid at {order.paid_at:%Y-%m-%d %H:%M}')
                continue

            if not notify_pending_dispatch(order, now=now):
                # Ningun canal configurado: dejarlo sin marcar para que el
                # proximo intento lo vuelva a tomar en vez de perderlo.
                self.stderr.write(f'Order {order.id}: no notification channel available.')
                continue

            order.dispatch_warned_at = now
            order.save(update_fields=['dispatch_warned_at'])
            warned += 1
            self.stdout.write(f'Order {order.id}: warned.')

        if options['dry_run']:
            self.stdout.write(f'{len(pending)} order(s) would be warned about.')
            return
        self.stdout.write(self.style.SUCCESS(f'Warned about {warned} order(s).'))

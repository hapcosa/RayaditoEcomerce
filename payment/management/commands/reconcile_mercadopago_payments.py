from django.core.management.base import BaseCommand, CommandError

from payment.models import Payments
from payment.services import MercadoPagoConfigurationError, sync_payment


class Command(BaseCommand):
    help = 'Reconcile local MercadoPago payments with the remote payment status.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-id',
            action='append',
            dest='payment_ids',
            help='MercadoPago payment id to reconcile. Can be passed more than once.',
        )

    def handle(self, *args, **options):
        payment_ids = options.get('payment_ids') or list(
            Payments.objects.filter(
                status__in=[
                    Payments.PaymentStatus.PENDING,
                    Payments.PaymentStatus.UNKNOWN,
                ],
            ).values_list('payment_id', flat=True),
        )
        if not payment_ids:
            self.stdout.write('No pending MercadoPago payments to reconcile.')
            return

        synced = 0
        failures = 0
        for payment_id in payment_ids:
            try:
                payment = sync_payment(payment_id)
            except MercadoPagoConfigurationError as exc:
                raise CommandError(str(exc)) from exc
            except Exception as exc:
                failures += 1
                self.stderr.write(f'Payment {payment_id}: {exc}')
                continue

            synced += 1
            self.stdout.write(
                f'Payment {payment.payment_id}: order {payment.order_id} -> {payment.status}',
            )

        if failures:
            raise CommandError(f'{failures} MercadoPago payment(s) could not be reconciled.')

        self.stdout.write(self.style.SUCCESS(f'Reconciled {synced} MercadoPago payment(s).'))

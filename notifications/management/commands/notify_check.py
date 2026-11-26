"""Revisa por que canales le llegaria a la duena el aviso de una venta.

Sin argumentos solo muestra el estado de cada canal (correo, push, WhatsApp),
sin secretos. Con --send manda un aviso de prueba por cada canal configurado:
es la forma de confirmar en produccion que de verdad llegan.

    python manage.py notify_check
    python manage.py notify_check --send
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from notifications import services, whatsapp, whatsapp_notices
from notifications.models import DevicePushToken

CONSOLE_BACKENDS = (
    'django.core.mail.backends.console.EmailBackend',
    'django.core.mail.backends.dummy.EmailBackend',
)


class Command(BaseCommand):
    help = 'Show which channels would notify the owner of a sale; --send tests them.'

    def add_arguments(self, parser):
        parser.add_argument('--send', action='store_true',
                            help='Send a test notice through every configured channel.')

    def _line(self, ok, text):
        mark = self.style.SUCCESS('OK  ') if ok else self.style.ERROR('NO  ')
        self.stdout.write(f'{mark}{text}')

    def handle(self, *args, **options):
        send = options['send']

        recipients = services.admin_recipients()
        smtp = settings.EMAIL_BACKEND not in CONSOLE_BACKENDS
        email_ok = bool(recipients) and smtp
        self._line(email_ok, f'Correo: {len(recipients)} destinatario(s) en ADMIN_NOTIFY_EMAILS'
                             f'{"" if smtp else ", pero EMAIL_BACKEND no manda correos"}')

        devices = DevicePushToken.objects.filter(is_active=True, user__is_staff=True)
        self._line(devices.exists(), f'Push: {devices.count()} aparato(s) de staff registrado(s)')

        phones = whatsapp_notices.admin_phones()
        wa_ok = whatsapp.is_enabled() and bool(phones)
        if not whatsapp.is_enabled():
            detail = 'apagado (WHATSAPP_ENABLED y credenciales)'
        else:
            detail = f'{len(phones)} celular(es) en ADMIN_WHATSAPP_PHONES'
        self._line(wa_ok, f'WhatsApp: {detail}')
        self.stdout.write(f'Recordatorio de despacho: cada {settings.DISPATCH_REMIND_HOURS} h '
                          'hasta que el pedido pase a "enviado".')

        if not send:
            self.stdout.write('Usa --send para mandar un aviso de prueba por cada canal.')
            return

        store = settings.STORE['name']
        if email_ok:
            ok = services.send_admin_mail(
                subject=f'Prueba de avisos — {store}',
                template='notifications/admin_test.txt', context={},
            )
            self._line(ok, 'Correo de prueba enviado' if ok else 'El correo fallo (ver log)')
        if devices.exists():
            delivered = services.push_admins(
                title=f'Prueba de avisos — {store}',
                body='Si ves esto, los avisos de venta llegan a este aparato.',
                data={'type': 'test'},
            )
            self._line(delivered > 0, f'Push entregado a {delivered} aparato(s)')
        if wa_ok:
            for phone in phones:
                try:
                    whatsapp.send_template(phone, whatsapp_notices.TEMPLATE_ADMIN_PENDING, {
                        'pedido': 'PRUEBA', 'cliente': store, 'plazo': 'esto es una prueba',
                    })
                    self._line(True, f'WhatsApp enviado a +{phone}')
                except whatsapp.WhatsAppError as exc:
                    self._line(False, f'WhatsApp a +{phone}: {exc}')

"""Token de acceso de Instagram: cargarlo, ver su estado y renovarlo.

    manage.py instagram_token set < token.txt   # o pegarlo y Ctrl-D
    manage.py instagram_token set --from-env    # migra INSTAGRAM_ACCESS_TOKEN del .env
    manage.py instagram_token status
    manage.py instagram_token refresh           # lo corre el timer diario

El token se lee por stdin y no como argumento: un argumento queda en el
historial del shell y lo ve cualquiera con `ps`.
"""
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from social import tokens
from social.models import InstagramToken


class Command(BaseCommand):
    help = 'Store, inspect or refresh the Instagram access token.'

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest='action', required=True)
        setter = sub.add_parser('set', help='Store a token read from stdin.')
        setter.add_argument('--from-env', action='store_true',
                            help='Use INSTAGRAM_ACCESS_TOKEN from the environment.')
        setter.add_argument('--expires-in-days', type=int, default=None,
                            help='Days until it expires, if known (a new token lasts 60).')
        sub.add_parser('status', help='Show expiry and last error, never the token.')
        refresher = sub.add_parser('refresh', help='Refresh it when it is close to expiring.')
        refresher.add_argument('--force', action='store_true',
                               help='Refresh now even if it is not due.')

    def handle(self, *args, action, **options):
        getattr(self, f'_{action}')(**options)

    def _set(self, from_env, expires_in_days, **options):
        token = settings.INSTAGRAM_ACCESS_TOKEN if from_env else sys.stdin.read()
        expires_in = expires_in_days * 86400 if expires_in_days else None
        try:
            tokens.save_token(token, expires_in=expires_in)
        except tokens.TokenError as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS('Token guardado (cifrado) en la base.'))
        if from_env:
            self.stdout.write('Ya puedes borrar INSTAGRAM_ACCESS_TOKEN del .env.')

    def _status(self, **options):
        row = InstagramToken.objects.filter(pk=1).first()
        if row is None:
            source = 'el .env' if settings.INSTAGRAM_ACCESS_TOKEN else 'ningún lado'
            self.stdout.write(f'No hay token en la base; se usa el de {source}.')
            return
        now = timezone.now()
        self.stdout.write(f'Obtenido/renovado: {timezone.localtime(row.issued_at):%Y-%m-%d %H:%M}')
        if row.expires_at:
            days = (row.expires_at - now).days
            self.stdout.write(
                f'Vence: {timezone.localtime(row.expires_at):%Y-%m-%d %H:%M} ({days} días)')
        else:
            self.stdout.write('Vence: desconocido (se aprende en la primera renovación)')
        if not tokens.refreshable():
            self.stdout.write('Host graph.facebook.com: token de usuario del sistema, no se renueva.')
        if not tokens.access_token():
            self.stdout.write(self.style.ERROR(
                'No se puede descifrar: ¿cambió SECRET_KEY? Vuelve a cargarlo.'))
        if row.last_error:
            self.stdout.write(self.style.WARNING(f'Último error: {row.last_error}'))

    def _refresh(self, force, **options):
        if not InstagramToken.objects.filter(pk=1).exists():
            # Instagram todavia no se conecto (o el token sigue en el .env): el
            # timer corre igual todos los dias y no debe fallar ni avisar.
            hint = ' Cárgalo con `instagram_token set --from-env`.' \
                if settings.INSTAGRAM_ACCESS_TOKEN else ''
            self.stdout.write(f'No hay token en la base; nada que renovar.{hint}')
            return
        try:
            renewed = tokens.refresh(force=force)
        except tokens.TokenError as exc:
            _alert(str(exc))
            raise CommandError(f'No se pudo renovar el token de Instagram: {exc}') from None
        if renewed:
            row = InstagramToken.objects.get(pk=1)
            until = f' hasta el {timezone.localtime(row.expires_at):%Y-%m-%d}' if row.expires_at else ''
            self.stdout.write(self.style.SUCCESS(f'Token renovado{until}.'))
        else:
            self.stdout.write('Todavía no toca renovarlo.')


def _alert(error):
    # Un push al staff: si nadie se entera, el token vence y las publicaciones
    # empiezan a fallar semanas despues.
    from notifications.services import push_admins
    try:
        push_admins(title='No se pudo renovar el token de Instagram',
                    body=error[:150], data={'type': 'instagram_token'})
    except Exception:  # el aviso nunca debe tapar el error original
        pass

"""Chequeos de despliegue propios del proyecto.

Corren con `manage.py check --deploy` y en el arranque. Existen porque los
errores que detectan no rompen nada al levantar el servidor: se descubren
cuando un cliente no recibe el mail de activacion o no puede pagar, o sea
tarde. Todos son inertes mientras `DEBUG=True`.
"""
import os

from django.conf import settings
from django.core.checks import Error, Warning, register

CONSOLE_EMAIL = 'django.core.mail.backends.console.EmailBackend'


@register(deploy=True)
def check_email_backend(app_configs, **kwargs):
    """Con el backend de consola nadie recibe nada.

    Djoser manda mail de activacion de cuenta y de reseteo de contraseña: si el
    backend imprime en la consola del servidor, registrarse y recuperar la
    clave quedan rotos sin que nada falle visiblemente.
    """
    if settings.DEBUG or settings.EMAIL_BACKEND != CONSOLE_EMAIL:
        return []
    return [Error(
        'EMAIL_BACKEND imprime los mails en consola en vez de enviarlos.',
        hint='Configura EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend '
             'junto con EMAIL_HOST, EMAIL_HOST_USER y EMAIL_HOST_PASSWORD. Sin '
             'esto, la activacion de cuenta y el reseteo de contraseña no '
             'llegan a nadie.',
        id='rayadito.E001',
    )]


@register(deploy=True)
def check_mercadopago_configured(app_configs, **kwargs):
    """Sin token no se puede cobrar."""
    if settings.DEBUG or os.environ.get('MERCADOPAGO_ACCESS_TOKEN'):
        return []
    return [Error(
        'Falta MERCADOPAGO_ACCESS_TOKEN: el checkout devuelve 500.',
        hint='Cargalo en el .env del servidor.',
        id='rayadito.E002',
    )]


@register(deploy=True)
def check_media_storage(app_configs, **kwargs):
    """La media en disco local no sobrevive a la perdida del servidor."""
    default_storage = settings.STORAGES['default']['BACKEND']
    if settings.DEBUG or default_storage != 'django.core.files.storage.FileSystemStorage':
        return []
    return [Warning(
        'Las fotos de producto se guardan en el disco del servidor.',
        hint='Configura MEDIA_STORAGE=s3 con las credenciales del bucket para '
             'moverlas a object storage. Mientras tanto, incluí MEDIA_ROOT en '
             'los backups.',
        id='rayadito.W001',
    )]

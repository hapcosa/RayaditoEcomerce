from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Registra los chequeos de despliegue (core/checks.py).
        from . import checks  # noqa: F401

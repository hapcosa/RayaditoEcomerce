from django.conf import settings
from django.db import models


class DevicePushToken(models.Model):
    """Un dispositivo del staff registrado para recibir push de Expo.

    La clave es el token, no el usuario: el dueno puede tener el APK en el
    telefono y en la tablet, y el mismo aparato puede cambiar de duena sin
    cambiar de token. Por eso el registro es un upsert por token.
    """

    class Platform(models.TextChoices):
        ANDROID = 'android', 'Android'
        IOS = 'ios', 'iOS'
        UNKNOWN = 'unknown', 'Desconocida'

    token = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='push_tokens',
    )
    platform = models.CharField(
        max_length=20, choices=Platform.choices, default=Platform.UNKNOWN,
    )
    # Lo apaga el propio Expo: cuando responde `DeviceNotRegistered` el aparato
    # desinstalo la app o revoco el permiso, y seguir mandandole es ruido.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_error = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'token de push'
        verbose_name_plural = 'tokens de push'

    def __str__(self):
        return f'{self.user} · {self.get_platform_display()}'

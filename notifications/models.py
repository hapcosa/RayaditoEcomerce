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


class WhatsAppOptIn(models.Model):
    """Consentimiento del cliente para recibir avisos de su pedido por WhatsApp.

    Va por pedido y no por usuario: la compra puede ser como invitado, y el
    telefono de un pedido no tiene por que ser el del perfil. Se guarda el texto
    exacto que acepto, para poder mostrar a que dijo que si.
    """

    order = models.OneToOneField(
        'orders.Order', on_delete=models.CASCADE, related_name='whatsapp_opt_in',
    )
    # Normalizado con `whatsapp.normalize_phone`: '569XXXXXXXX'.
    phone = models.CharField(max_length=20)
    consent_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Baja: el cliente pidio no recibir mas avisos. No se borra la fila, para
    # que quede constancia de que hubo consentimiento y de cuando se retiro.
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'consentimiento de WhatsApp'
        verbose_name_plural = 'consentimientos de WhatsApp'

    def __str__(self):
        return f'Pedido #{self.order_id} · +{self.phone}'

    @property
    def is_active(self):
        return self.revoked_at is None


class WhatsAppMessage(models.Model):
    """Un aviso por WhatsApp enviado (o intentado) para un pedido.

    `key` identifica el aviso dentro del pedido ('paid_order', 'shipped') y es
    unico por pedido: MercadoPago reenvia la misma aprobacion varias veces, y
    cada mensaje se cobra (precio por mensaje desde el 2025-07-01).
    """

    class Status(models.TextChoices):
        SENDING = 'sending', 'Enviando'
        SENT = 'sent', 'Enviado'
        FAILED = 'failed', 'Fallido'

    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='whatsapp_messages',
    )
    key = models.CharField(max_length=50)
    template = models.CharField(max_length=100)
    to = models.CharField(max_length=20)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.SENDING,
    )
    # Id que devuelve Meta ('wamid.…'); lo traen los webhooks de estado.
    wamid = models.CharField(max_length=255, blank=True, default='')
    error = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'mensaje de WhatsApp'
        verbose_name_plural = 'mensajes de WhatsApp'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'key'], name='whatsapp_message_once_per_order',
            ),
        ]

    def __str__(self):
        return f'Pedido #{self.order_id} · {self.key} · {self.get_status_display()}'

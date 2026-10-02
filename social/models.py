from django.conf import settings
from django.db import models
from django.utils import timezone


class InstagramPost(models.Model):
    """Una publicacion de producto en la cuenta de Instagram de la tienda.

    La app la crea programada (para ya o para mas tarde) y el comando
    `publish_instagram`, que corre desde un timer de systemd, es el unico que
    habla con Meta. Asi el request de la app no queda colgado los segundos que
    Instagram tarda en procesar las fotos.
    """

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Programada'
        PUBLISHING = 'publishing', 'Publicando'
        PUBLISHED = 'published', 'Publicada'
        FAILED = 'failed', 'Fallida'
        CANCELLED = 'cancelled', 'Cancelada'

    product = models.ForeignKey(
        'product.Product', on_delete=models.CASCADE,
        related_name='instagram_posts',
    )
    caption = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED,
        db_index=True,
    )
    scheduled_for = models.DateTimeField(default=timezone.now, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    # Id que devuelve `media_publish`. Se guarda apenas Meta lo entrega: con
    # este id la publicacion ya existe en Instagram, pase lo que pase despues.
    media_id = models.CharField(max_length=64, blank=True, default='')
    permalink = models.URLField(blank=True, default='')
    last_error = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Cuando la tomo el comando. Sirve para detectar una corrida que murio a
    # mitad de camino (ver services.recover_stuck_posts).
    started_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-scheduled_for']
        verbose_name = 'publicación de Instagram'
        verbose_name_plural = 'publicaciones de Instagram'

    def __str__(self):
        return f'{self.product} · {self.get_status_display()}'


class InstagramToken(models.Model):
    """Token de larga duracion de Instagram Login. Una sola fila (pk=1).

    Vive en la base y no en el `.env` para que `manage.py instagram_token
    refresh` lo pueda renovar solo: el token vence a los 60 dias y editar el
    `.env` exige reiniciar el servicio. Se guarda cifrado con una clave
    derivada de SECRET_KEY (ver social/tokens.py), asi que un dump de la base
    —los backups se copian fuera del servidor— no lleva un token usable.
    """

    encrypted_token = models.TextField()
    # Cuando se obtuvo o se renovo. Meta solo renueva tokens con 24 h o mas.
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    last_refresh_attempt = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'token de Instagram'
        verbose_name_plural = 'token de Instagram'

    def __str__(self):
        return f'Token de Instagram (vence {self.expires_at:%Y-%m-%d})' if self.expires_at \
            else 'Token de Instagram'

from django.conf import settings
from django.db import models


class Suggestion(models.Model):
    """Buzón de sugerencias: mensajes que dejan los visitantes o clientes.

    El envío es público (anónimo permitido). Si el usuario está autenticado
    se enlaza con `user`. La moderación se hace cambiando `status`.
    """

    class Kind(models.TextChoices):
        SUGERENCIA = 'sugerencia', 'Sugerencia'
        RECLAMO = 'reclamo', 'Reclamo'
        FELICITACION = 'felicitacion', 'Felicitación'
        OTRO = 'otro', 'Otro'

    class Status(models.TextChoices):
        NEW = 'new', 'Nueva'
        REVIEWED = 'reviewed', 'Revisada'
        ARCHIVED = 'archived', 'Archivada'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='suggestions',
    )
    name = models.CharField(max_length=120, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SUGERENCIA)
    message = models.TextField(max_length=2000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sugerencia'
        verbose_name_plural = 'Sugerencias'

    def __str__(self):
        who = self.name or self.email or 'anónima'
        return f'{self.get_kind_display()} · {who} · {self.created_at:%Y-%m-%d}'

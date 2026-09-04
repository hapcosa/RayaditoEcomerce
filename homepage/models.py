from django.core.exceptions import ValidationError
from django.db import models


class HeroImage(models.Model):
    """Una de las fotos de portada que el dueño sube desde la app admin.

    Se muestran hasta `MAX_ACTIVAS` a la vez, escalonadas. El limite es de
    presentacion, no de almacenamiento: se pueden guardar mas y activar las que
    se quieran mostrar, para poder rotar la portada sin volver a subir fotos.
    """

    MAX_ACTIVAS = 3

    image = models.ImageField(upload_to='portada/%y/%m')
    # Texto alternativo: sin esto la portada queda muda para un lector de
    # pantalla, que es justamente donde vive el contenido principal del sitio.
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = 'foto de portada'
        verbose_name_plural = 'fotos de portada'

    def __str__(self):
        return self.alt_text or self.caption or f'Foto de portada {self.pk}'

    def clean(self):
        """Impide activar una cuarta foto.

        Va en `clean()` y no en el serializer para que tambien aplique desde el
        admin de Django y desde un shell, no solo desde la API.
        """
        if not self.is_active:
            return
        activas = HeroImage.objects.filter(is_active=True).exclude(pk=self.pk).count()
        if activas >= self.MAX_ACTIVAS:
            raise ValidationError(
                {'is_active': f'Ya hay {self.MAX_ACTIVAS} fotos de portada activas. '
                              'Desactiva una antes de activar esta.'}
            )

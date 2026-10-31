from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from core.images import shrink_upload


class HomepageSettings(models.Model):
    """Ajustes de la portada que la dueña cambia desde la app. Fila única."""

    # El mosaico de la web tiene una composicion dibujada para cada cantidad
    # entre estos topes (ver web/components/home/HeroMosaic.tsx): fuera de
    # ese rango la portada se deformaria.
    MIN_HERO_PHOTOS = 3
    MAX_HERO_PHOTOS = 7
    DEFAULT_HERO_PHOTOS = 5

    hero_max_photos = models.PositiveSmallIntegerField(
        default=DEFAULT_HERO_PHOTOS,
        validators=[MinValueValidator(MIN_HERO_PHOTOS), MaxValueValidator(MAX_HERO_PHOTOS)],
        help_text='Cuántas fotos muestra la portada como máximo.',
    )

    class Meta:
        verbose_name = 'ajustes de portada'
        verbose_name_plural = 'ajustes de portada'

    def __str__(self):
        return 'Ajustes de portada'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        """Guarda y, si el tope bajo, archiva las fotos activas que sobran.

        Sobran las ultimas en el orden de la portada: las primeras son las que
        la dueña puso adelante. Se archivan, no se borran.
        """
        self.pk = 1
        with transaction.atomic():
            previo = (
                HomepageSettings.objects.filter(pk=1)
                .values_list('hero_max_photos', flat=True).first()
            )
            super().save(*args, **kwargs)
            # Solo al bajar: crear la fila (primer `load()`) no toca la portada.
            if previo is None or self.hero_max_photos >= previo:
                return
            sobrantes = HeroImage.objects.filter(is_active=True)[self.hero_max_photos:]
            HeroImage.objects.filter(pk__in=[h.pk for h in sobrantes]).update(is_active=False)


def hero_max_photos():
    """Tope vigente de fotos activas en la portada."""
    return HomepageSettings.load().hero_max_photos


class HeroImage(models.Model):
    """Una de las fotos de portada que el dueño sube desde la app admin.

    Se muestran hasta `hero_max_photos()` a la vez, escalonadas (lo elige la
    dueña entre 3 y 7). El limite es de presentacion, no de almacenamiento: se
    pueden guardar mas y activar las que se quieran mostrar, para poder rotar
    la portada sin volver a subir fotos.
    """

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

    def save(self, *args, **kwargs):
        shrink_upload(self.image)
        super().save(*args, **kwargs)

    def clean(self):
        """Impide activar mas fotos que el tope de la portada.

        Va en `clean()` y no en el serializer para que tambien aplique desde el
        admin de Django y desde un shell, no solo desde la API.
        """
        if not self.is_active:
            return
        tope = hero_max_photos()
        activas = HeroImage.objects.filter(is_active=True).exclude(pk=self.pk).count()
        if activas >= tope:
            raise ValidationError(
                {'is_active': f'Ya hay {tope} fotos de portada activas. '
                              'Desactiva una antes de activar esta.'}
            )

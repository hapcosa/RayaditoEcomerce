from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):
    """Una dirección de la libreta del usuario.

    El modelo es una libreta, no un perfil: un usuario tiene varias filas y las
    reutiliza al comprar (`orders.Order.profile` apunta a la que se usó, con
    `DO_NOTHING`, así que borrar una dirección no toca los pedidos viejos).
    """

    class Meta:
        ordering = ('-is_default', 'id')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    # Alias para reconocerla en la lista ("Casa", "Taller"). Opcional.
    label = models.CharField(max_length=60, blank=True, default='')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255, default='')
    city = models.CharField(max_length=255, default='')
    zipcode = models.CharField(max_length=20, blank=True, default='')
    phone = models.CharField(max_length=255, default='')
    # Guarda la **región** chilena (ej. "Los Lagos"), no un país: el nombre
    # viene del modelo original y lo usan órdenes ya emitidas, así que se
    # mantiene. Texto libre a propósito (ver `shipping.locations`).
    country_region = models.CharField(max_length=255, default='')
    # La dirección que el checkout preselecciona. Una sola por usuario.
    is_default = models.BooleanField(default=False)

    def __str__(self):
        etiqueta = self.label or self.address_line_1
        return f'{etiqueta} ({self.user_id})'

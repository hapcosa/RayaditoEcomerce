from django.db import models


class Shipping(models.Model):
    class Meta:
        verbose_name = 'Shipping'
        verbose_name_plural = 'Shipping'

    class Carrier(models.TextChoices):
        manual = 'manual', 'Precio fijo'
        starken = 'starken', 'Starken (cotizado)'

    class DeliveryType(models.IntegerChoices):
        # Codigos de Starken (tipoEntrega).
        agency = 1, 'Retiro en agencia'
        home = 2, 'A domicilio'

    name = models.CharField(max_length=255, unique=True)
    time_to_delivery = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    # Con carrier=starken y la integracion activa este precio no se usa: se
    # cotiza por comuna. Con la integracion apagada, la opcion no se ofrece.
    price = models.PositiveIntegerField(default=0)
    # Opcional: opciones como "Retiro en taller" no tienen logo, y sin esto
    # no se pueden crear desde /admin/ ni desde un seed.
    photo = models.ImageField(upload_to='logos/%y/%m', blank=True, null=True)
    carrier = models.CharField(
        max_length=20, choices=Carrier.choices, default=Carrier.manual,
        help_text='Precio fijo, o cotizado en linea con el courier por comuna.',
    )
    starken_delivery_type = models.PositiveSmallIntegerField(
        choices=DeliveryType.choices, null=True, blank=True,
        help_text='Solo para Starken: retiro en agencia o a domicilio.',
    )
    starken_service_type = models.PositiveSmallIntegerField(
        default=0, help_text='Solo para Starken: 0 = normal, 1 = express.',
    )

    def __str__(self):
        return self.name

    @property
    def is_starken(self):
        return self.carrier == self.Carrier.starken


class Shipment(models.Model):
    """Orden de flete de un pedido en el courier y su ultimo estado conocido.

    Vive aparte de `Order` para que el seguimiento (estado, si ya termino) no
    llene el pedido de columnas que solo usa un courier. El numero de
    seguimiento se copia ademas a `Order.deliveryNumber`, que es el que ven la
    app admin y la pagina del pedido.
    """
    order = models.OneToOneField(
        'orders.Order', on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=20, default=Shipping.Carrier.starken)
    tracking_number = models.CharField(max_length=32, db_index=True)
    status = models.CharField(max_length=120, blank=True)
    status_at = models.DateTimeField(null=True, blank=True)
    # Estado terminal (entregado, devuelto, anulado...): ya no se consulta.
    is_final = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.carrier} {self.tracking_number}'

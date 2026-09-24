from django.db import models
from product.models import Product
from .countries import Countries
from datetime import datetime
from django.contrib.auth import get_user_model
from user_profile.models import UserProfile
from shipping.models import Shipping
User = get_user_model()


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        not_processed = 'no procesado'
        processed = 'procesado'
        shipping = 'enviado'
        cancelled = 'cancelado'
        refused = 'rechazado'
    status = models.CharField(
        max_length=50, choices=OrderStatus.choices, default=OrderStatus.not_processed)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    email=models.EmailField(blank=True, null=True)
    transaction_id = models.CharField(max_length=255, null=True)
    amount = models.PositiveIntegerField(null=True)  # total en entero CLP
    shipping_price = models.PositiveIntegerField(default=0)  # costo de envio en entero CLP
    full_name = models.CharField(max_length=255, blank=True, null=True)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    postal_zip_code = models.CharField(max_length=20, blank=True)
    region = models.CharField(
        max_length=255, choices=Countries.choices, default=Countries.cero, blank=True)
    telephone_number = models.CharField(max_length=255, blank=True)
    shipping_id = models.ForeignKey(Shipping, on_delete=models.DO_NOTHING, blank=True, null=True)
    date_issued = models.DateTimeField(auto_now_add=datetime.now)
    # `date_issued` es cuando se creo el pedido, no cuando se pago: entre uno y
    # otro puede no pasar nada nunca (el cliente abandona el checkout). El reloj
    # de despacho se cuenta desde `paid_at`.
    paid_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Primera vez que MercadoPago aprobo el pago. Null = nunca se pago.',
    )
    shipped_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Cuando el pedido paso a "enviado".',
    )
    # Lo escribe el aviso de plazo de despacho por vencer (comando programado),
    # para no repetir el mismo aviso en cada corrida. Todavia no lo setea nadie.
    dispatch_warned_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Ultimo aviso al admin de que el plazo de despacho esta por vencer.',
    )
    profile = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, null=True )
    deliveryNumber = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if (self.transaction_id is None):
            return str(self.id)
        else:
            return str(self.transaction_id)


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.PositiveIntegerField()  # entero CLP
    count = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=datetime.now)

    def __str__(self):
        return str(self.product)

from django.db import models
from django.core.validators import MinValueValidator
from product.models import Product
from django.conf import settings
User = settings.AUTH_USER_MODEL
class Carrito(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Suma de las cantidades de todos los items (no de productos distintos).
    total_items = models.IntegerField(default=0)
class CarritoItem(models.Model):
    carrito= models.ForeignKey(Carrito, on_delete=models.CASCADE)
    product= models.ForeignKey(Product, on_delete=models.CASCADE)
    # Cantidad de este producto en el carrito. El front lo llama "count".
    count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['carrito', 'product'],
                                    name='unique_product_per_cart'),
        ]


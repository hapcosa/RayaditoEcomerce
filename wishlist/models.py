from django.conf import settings
from django.db import models

from product.models import Product


class WishlistItem(models.Model):
    """Producto guardado en la lista de deseos de un usuario.

    Un usuario no puede guardar dos veces el mismo producto (unique).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto deseado'
        verbose_name_plural = 'Lista de deseos'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_wishlist_item_per_user_product',
            ),
        ]

    def __str__(self):
        return f'{self.user} ♥ {self.product}'

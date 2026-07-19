from django.db import models
from datetime import datetime
from decimal import Decimal
from category.models import Category
from metaproduct.models import *
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

class Product(models.Model):
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='photos/%y/%m')
    description = models.TextField()
    # Dinero en entero CLP (peso chileno, sin decimales). Ver AGENTS.md.
    price = models.PositiveIntegerField()
    compare_price = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sold = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=datetime.now)

    def __str__(self):
        return self.name

class Joyas(Product):
    class Meta:
        verbose_name = 'Joyas'
        verbose_name_plural = 'Joyas'
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

class Piedras(Product):
    class Meta:
        verbose_name = 'Piedras'
        verbose_name_plural = 'Piedras'
    large = models.DecimalField(max_digits=5, decimal_places=2)
    width = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    nombrePiedra = models.ForeignKey(NombrePiedra, on_delete=models.CASCADE)

#clases relacionales muchos a muchos o muchos  a uno
class RelationPiedraJoya(models.Model):
    class Meta:
        verbose_name = 'Piedrasin'
        verbose_name_plural = 'Piedrasin'
    nombrePiedra = models.ForeignKey(NombrePiedra, on_delete=models.CASCADE)
    joya = models.ForeignKey(Joyas, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

class GalleryProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    photos = models.ImageField(upload_to='photos/%y/%m')
class JoyaMateriales(models.Model):
    joya = models.ForeignKey(Joyas , on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)


class Review(models.Model):
    """Reseña con puntuación (0.5–5.0, medias estrellas) de un usuario a un producto."""
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1,
        validators=[MinValueValidator(Decimal('0.5')), MaxValueValidator(Decimal('5.0'))],
    )
    comment = models.TextField(blank=True, default='')
    verified_purchase = models.BooleanField(default=False)
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_review_per_user_product',
            ),
        ]

    def __str__(self):
        return f'{self.product} - {self.user} ({self.rating})'

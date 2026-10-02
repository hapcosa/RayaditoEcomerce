from datetime import datetime
from decimal import Decimal

from django.db import models
from django.db.models import OuterRef, Q, Subquery, Sum
from category.models import Category
from metaproduct.models import *
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class AttributeKind(models.TextChoices):
    SELECT = 'select', 'Selección'
    TEXT = 'text', 'Texto'
    INTEGER = 'integer', 'Entero'
    DECIMAL = 'decimal', 'Decimal'


class ProductQuerySet(models.QuerySet):
    """Filtros de inventario que se resuelven en la base.

    Mismo criterio que `Product.available_stock`: si el producto tiene
    variantes activas manda la suma de su stock; si no, `Product.stock`.
    """

    def with_available_stock(self):
        # Subquery y no Sum sobre el JOIN: el catalogo encadena filtros por
        # atributos y `distinct()`, y un GROUP BY en la consulta principal se
        # mezclaria con ellos.
        variant_stock = (
            ProductVariant.objects
            .filter(product=OuterRef('pk'), is_active=True)
            .order_by()
            .values('product')
            .annotate(total=Sum('stock'))
            .values('total')
        )
        return self.annotate(_variant_stock=Subquery(variant_stock))

    def available(self):
        return self.with_available_stock().filter(
            Q(_variant_stock__isnull=True, stock__gt=0) | Q(_variant_stock__gt=0))

    def sold_out(self):
        return self.with_available_stock().filter(
            Q(_variant_stock__isnull=True, stock=0) | Q(_variant_stock=0))


class Product(models.Model):
    class ProductStatus(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PUBLISHED = 'published', 'Publicado'
        ARCHIVED = 'archived', 'Archivado'

    class ProductType(models.TextChoices):
        # Define en que catalogo publico aparece el producto. `GENERAL` es el
        # estado heredado: productos sin clasificar, que no se listan en /joyas
        # ni en /piedras hasta que el staff les asigne un tipo.
        JOYA = 'joya', 'Joya'
        PIEDRA = 'piedra', 'Piedra'
        GENERAL = 'general', 'Sin clasificar'

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    product_type = models.SlugField(
        max_length=55, choices=ProductType.choices,
        default=ProductType.GENERAL, db_index=True,
    )
    photo = models.ImageField(upload_to='photos/%y/%m')
    description = models.TextField()
    # Dinero en entero CLP (peso chileno, sin decimales). Ver AGENTS.md.
    price = models.PositiveIntegerField()
    compare_price = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # Unidades disponibles. En joyeria casi siempre es 1 (pieza unica) o 0
    # (vendida). Si el producto tiene variantes activas, manda la suma de las
    # variantes y este campo no se usa (ver `available_stock`).
    stock = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=ProductStatus.choices, default=ProductStatus.PUBLISHED,
        db_index=True,
    )
    is_featured = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=datetime.now)

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return self.name

    @property
    def available_stock(self):
        stock = self.variants.filter(is_active=True).aggregate(total=Sum('stock'))['total']
        if stock is not None:
            return stock
        return self.stock

    @property
    def sold(self):
        """Agotado. Derivado del stock; ya no es un campo que se escriba."""
        return self.available_stock == 0

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'producto'
            candidate = base_slug[:255]
            suffix = 2
            while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                suffix_text = f'-{suffix}'
                candidate = f'{base_slug[:255 - len(suffix_text)]}{suffix_text}'
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class Attribute(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    unit = models.CharField(max_length=30, blank=True, default='')
    kind = models.CharField(
        max_length=20, choices=AttributeKind.choices, default=AttributeKind.SELECT,
    )
    is_variant_option = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute, related_name='values', on_delete=models.CASCADE,
    )
    value = models.CharField(max_length=255)
    numeric_value = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['attribute__sort_order', 'sort_order', 'value']
        constraints = [
            models.UniqueConstraint(
                fields=['attribute', 'value'],
                name='unique_value_per_attribute',
            ),
        ]

    def __str__(self):
        return f'{self.attribute}: {self.value}'


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(
        Product, related_name='attribute_values', on_delete=models.CASCADE,
    )
    attribute_value = models.ForeignKey(
        AttributeValue, related_name='products', on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'attribute_value'],
                name='unique_attribute_value_per_product',
            ),
        ]

    def __str__(self):
        return f'{self.product} - {self.attribute_value}'


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, related_name='variants', on_delete=models.CASCADE,
    )
    sku = models.CharField(max_length=100, blank=True, default='')
    price_override = models.PositiveIntegerField(null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    attributes = models.ManyToManyField(
        AttributeValue, through='ProductVariantAttributeValue',
        related_name='variants', blank=True,
    )
    date_created = models.DateTimeField(auto_now_add=datetime.now)

    class Meta:
        ordering = ['product_id', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'sku'],
                condition=~Q(sku=''),
                name='unique_variant_sku_per_product',
            ),
        ]

    @property
    def effective_price(self):
        if self.price_override is not None:
            return self.price_override
        return self.product.price

    def __str__(self):
        return self.sku or f'{self.product} variant {self.id}'


class ProductVariantAttributeValue(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['variant', 'attribute_value'],
                name='unique_attribute_value_per_variant',
            ),
        ]

    def __str__(self):
        return f'{self.variant} - {self.attribute_value}'

class GalleryProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    photos = models.ImageField(upload_to='photos/%y/%m')


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

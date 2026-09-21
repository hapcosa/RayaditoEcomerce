from django.db import models


# Create your models here.
class Category(models.Model):
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, unique=True)
    ProductType = models.CharField(max_length=55)
    # Qué atributos aplican a los productos de esta categoría: "Anillos" usa
    # Talla y Color, "Piedras" usa alto/ancho/largo. Se hereda hacia las hijas
    # (ver `effective_attributes`). Referencia por string para no ciclar el
    # import: product.models ya importa category.models.
    attributes = models.ManyToManyField(
        'product.Attribute', through='CategoryAttribute',
        related_name='categories', blank=True,
    )

    def __str__(self):
        return self.name

    def ancestors(self):
        """Cadena de ancestros, de la madre inmediata hacia la raíz.

        Corta si el árbol tiene un ciclo: el modelo no lo impide a nivel de BD
        (solo lo valida el serializer admin), y acá un ciclo colgaría el server.
        """
        chain = []
        seen = {self.pk}
        node = self.parent
        while node is not None and node.pk not in seen:
            chain.append(node)
            seen.add(node.pk)
            node = node.parent
        return chain

    def effective_attributes(self):
        """`CategoryAttribute` propios + heredados, ya resueltos.

        Lo propio gana sobre lo heredado para el mismo atributo, y lo más
        cercano en el árbol gana sobre lo más lejano: así una hija puede volver
        opcional un atributo que la madre marcó obligatorio.
        """
        resolved = {}
        for node in [self, *self.ancestors()]:
            for link in node.category_attributes.select_related('attribute'):
                resolved.setdefault(link.attribute_id, link)
        return sorted(
            resolved.values(),
            key=lambda link: (link.sort_order, link.attribute.sort_order, link.attribute.name),
        )


class CategoryAttribute(models.Model):
    """Atributo aplicable a una categoría, opcional u obligatorio."""
    category = models.ForeignKey(
        Category, related_name='category_attributes', on_delete=models.CASCADE,
    )
    attribute = models.ForeignKey(
        'product.Attribute', related_name='category_links', on_delete=models.CASCADE,
    )
    # Obligatorio == la app admin no deja publicar el producto sin cargarlo.
    is_required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'attribute'],
                name='unique_attribute_per_category',
            ),
        ]

    def __str__(self):
        return f'{self.category} - {self.attribute}'

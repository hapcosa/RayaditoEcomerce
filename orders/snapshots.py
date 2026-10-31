"""Foto de la pieza vendida para los reportes de ventas.

`OrderItem` ya guardaba `name` y `price` del momento de la compra; esto suma la
categoria, el catalogo, el costo y los atributos. Asi un reporte de "ventas por
piedra en marzo" no cambia porque la duena reclasifique la pieza en abril.
"""
from .models import OrderItemAttribute


def snapshot_order_item(item):
    """Copia al item los datos de su producto que miran los reportes."""
    product = item.product
    item.category_name = product.category.name if product.category_id else ''
    item.catalog = product.product_type or ''
    item.unit_cost = product.cost
    item.save(update_fields=['category_name', 'catalog', 'unit_cost'])

    item.attributes.all().delete()
    values = (
        product.attribute_values
        .select_related('attribute_value__attribute')
        .order_by('attribute_value__attribute__sort_order', 'attribute_value__sort_order')
    )
    OrderItemAttribute.objects.bulk_create([
        OrderItemAttribute(
            item=item,
            attribute_slug=link.attribute_value.attribute.slug,
            attribute_name=link.attribute_value.attribute.name,
            value=link.attribute_value.value,
        )
        for link in values
    ])

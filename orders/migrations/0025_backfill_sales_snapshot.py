"""Rellena la foto de las ventas que ya existian con los datos actuales.

Es lo mejor que se puede reconstruir: si una pieza vieja cambio de categoria,
el pasado queda con la categoria de hoy. Las ventas nuevas ya nacen con su
foto (ver `orders.snapshots`). El costo no se rellena: no existia.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    OrderItem = apps.get_model('orders', 'OrderItem')
    OrderItemAttribute = apps.get_model('orders', 'OrderItemAttribute')
    ProductAttributeValue = apps.get_model('product', 'ProductAttributeValue')

    items = OrderItem.objects.select_related('product__category').filter(
        category_name='', catalog='',
    )
    for item in items.iterator():
        product = item.product
        item.category_name = product.category.name if product.category_id else ''
        item.catalog = product.product_type or ''
        item.save(update_fields=['category_name', 'catalog'])

        links = ProductAttributeValue.objects.filter(product_id=product.pk).select_related(
            'attribute_value__attribute',
        )
        OrderItemAttribute.objects.bulk_create([
            OrderItemAttribute(
                item=item,
                attribute_slug=link.attribute_value.attribute.slug,
                attribute_name=link.attribute_value.attribute.name,
                value=link.attribute_value.value,
            )
            for link in links
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0024_sales_snapshot'),
        ('product', '0016_product_cost'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]

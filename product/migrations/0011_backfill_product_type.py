"""Clasifica los productos existentes segun su subclase multi-table.

Antes de esta migracion `product_type` era un slug libre que quedaba en
'general' para todos, mientras el catalogo publico legacy distinguia joyas de
piedras por la existencia de una fila en las tablas hijas `Joyas` / `Piedras`.
El backfill traduce ese contrato implicito al campo, que ahora es la fuente de
verdad para ambos catalogos.

Los productos sin fila en ninguna subclase (los que crea la app admin Expo)
quedan deliberadamente en 'general': no hay forma de inferir su tipo, y
marcarlos al azar los publicaria en el catalogo equivocado. El staff los
clasifica desde la app.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    Joyas = apps.get_model('product', 'Joyas')
    Piedras = apps.get_model('product', 'Piedras')

    joya_ids = set(Joyas.objects.values_list('product_ptr_id', flat=True))
    piedra_ids = set(Piedras.objects.values_list('product_ptr_id', flat=True))

    Product.objects.filter(id__in=joya_ids).update(product_type='joya')
    Product.objects.filter(id__in=piedra_ids - joya_ids).update(
        product_type='piedra')


def unbackfill(apps, schema_editor):
    # El valor previo era 'general' para todos los productos.
    Product = apps.get_model('product', 'Product')
    Product.objects.filter(product_type__in=['joya', 'piedra']).update(
        product_type='general')


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_alter_product_product_type'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]

"""`Product.sold` (booleano) pasa a `Product.stock` (entero).

Una pieza vendida queda con stock 0 y una disponible con 1: es lo que
`available_stock` ya devolvia para productos sin variantes. `sold` sigue
existiendo como propiedad derivada del modelo.
"""
from django.db import migrations, models


def sold_to_stock(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    Product.objects.filter(sold=True).update(stock=0)
    Product.objects.filter(sold=False).update(stock=1)


def stock_to_sold(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    Product.objects.filter(stock=0).update(sold=True)
    Product.objects.filter(stock__gt=0).update(sold=False)


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_drop_product_subclasses'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(sold_to_stock, stock_to_sold),
        migrations.RemoveField(
            model_name='product',
            name='sold',
        ),
    ]

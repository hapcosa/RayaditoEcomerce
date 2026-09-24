"""Pasa los datos de las subclases `Joyas`/`Piedras` a atributos del producto.

Las subclases eran de herencia multitabla: cada joya y cada piedra ya es un
`Product`, y lo unico que vive en la tabla hija son sus campos propios
(material/peso, largo/ancho/alto/tipo de piedra). Eso es exactamente lo que
ahora expresa `ProductAttributeValue`, asi que la fila hija queda de mas.

Los atributos destino ya vienen sembrados por `0009_generic_product_variants`;
esta migracion solo crea los **valores** que falten y los engancha al producto.
"""
from decimal import Decimal

from django.db import migrations

# Campo de la subclase -> slug del atributo sembrado en 0009.
MEDIDAS_JOYA = [('weight', 'peso')]
MEDIDAS_PIEDRA = [('large', 'largo'), ('width', 'ancho'), ('height', 'alto')]


def texto_es_cl(numero):
    """`Decimal('12.50')` -> `'12,5'`: como lo escribiria el staff en es-CL."""
    limpio = numero.normalize()
    # normalize() deja 2E+1 para 20; el formato 'f' lo devuelve a 20.
    return f'{limpio:f}'.replace('.', ',')


def enganchar(apps, producto, slug, texto, numero):
    """Deja el producto con ese valor del atributo. Idempotente."""
    Attribute = apps.get_model('product', 'Attribute')
    AttributeValue = apps.get_model('product', 'AttributeValue')
    ProductAttributeValue = apps.get_model('product', 'ProductAttributeValue')

    atributo = Attribute.objects.filter(slug=slug).first()
    if atributo is None:
        # Una base sin la siembra de 0009 no es motivo para abortar el deploy:
        # el atributo se puede crear despues desde la app admin.
        return
    valor, _ = AttributeValue.objects.get_or_create(
        attribute=atributo, value=texto, defaults={'numeric_value': numero},
    )
    ProductAttributeValue.objects.get_or_create(
        product=producto, attribute_value=valor,
    )


def migrar(apps, schema_editor):
    Joyas = apps.get_model('product', 'Joyas')
    Piedras = apps.get_model('product', 'Piedras')
    Product = apps.get_model('product', 'Product')

    for joya in Joyas.objects.select_related('material'):
        producto = Product.objects.get(pk=joya.product_ptr_id)
        if joya.material_id:
            enganchar(apps, producto, 'material', joya.material.name, None)
        for campo, slug in MEDIDAS_JOYA:
            numero = getattr(joya, campo)
            if numero is not None:
                enganchar(apps, producto, slug, texto_es_cl(numero), numero)

    for piedra in Piedras.objects.select_related('nombrePiedra'):
        producto = Product.objects.get(pk=piedra.product_ptr_id)
        tipo = piedra.nombrePiedra if piedra.nombrePiedra_id else None
        if tipo is not None:
            enganchar(apps, producto, 'nombre-piedra', tipo.name, None)
            # La dureza y el origen colgaban del tipo de piedra, no de la
            # pieza; al desarmar la subclase se copian al producto.
            if tipo.mohs is not None:
                enganchar(apps, producto, 'dureza-mohs', texto_es_cl(tipo.mohs), tipo.mohs)
            if tipo.origen:
                enganchar(apps, producto, 'origen', tipo.origen, None)
        for campo, slug in MEDIDAS_PIEDRA:
            numero = getattr(piedra, campo)
            if numero is not None:
                enganchar(apps, producto, slug, texto_es_cl(numero), numero)


def deshacer(apps, schema_editor):
    """No se revierte.

    Los valores migrados son indistinguibles de los que el staff cargue a mano
    desde la app admin, asi que borrarlos destruiria datos buenos. Revertir la
    migracion deja los productos con sus atributos, que es lo correcto.
    """


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_backfill_product_type'),
        ('metaproduct', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrar, deshacer),
    ]

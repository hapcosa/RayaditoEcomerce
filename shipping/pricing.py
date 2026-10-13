"""Precio de cada opcion de envio, en entero CLP.

Una sola funcion decide el precio para lo que ve el cliente (opciones del
checkout) y para lo que se cobra (al crear la orden), asi que no pueden
divergir: el precio nunca viene del navegador.
"""
import logging

from . import starken
from .models import Shipping

logger = logging.getLogger(__name__)


class ShippingUnavailable(Exception):
    """La opcion no se puede cotizar para ese destino ahora."""


def price_for(shipping, commune):
    if not shipping.is_starken:
        return int(shipping.price or 0)
    if not starken.is_enabled():
        raise ShippingUnavailable('Starken no esta activado')
    if not shipping.starken_delivery_type:
        raise ShippingUnavailable(f'la opcion {shipping.name!r} no dice si es a domicilio o agencia')
    if not (commune or '').strip():
        raise ShippingUnavailable('falta la comuna de destino para cotizar')
    try:
        return starken.quote(commune, shipping.starken_delivery_type,
                             shipping.starken_service_type)
    except starken.StarkenError as exc:
        raise ShippingUnavailable(str(exc)) from exc


def options_for(commune=None):
    """[(opcion, precio)] ofrecibles para la comuna, de menor a mayor precio.

    Las de Starken sin comuna, con la integracion apagada o con la API caida
    se omiten: las de precio fijo siguen disponibles y el checkout no se cae.
    """
    priced = []
    for shipping in Shipping.objects.order_by('price', 'name'):
        try:
            priced.append((shipping, price_for(shipping, commune)))
        except ShippingUnavailable as exc:
            if shipping.is_starken and starken.is_enabled() and commune:
                logger.warning('Envio %s sin cotizar para %r: %s', shipping.pk, commune, exc)
    return sorted(priced, key=lambda pair: (pair[1], pair[0].name))

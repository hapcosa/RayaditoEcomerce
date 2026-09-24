from django import template

from notifications.formatting import clp as format_clp

register = template.Library()


@register.filter(name='clp')
def clp(value):
    """Entero CLP con puntos de miles. Solo presentacion."""
    return format_clp(value)

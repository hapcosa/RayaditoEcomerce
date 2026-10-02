"""RUT chileno: limpiar, validar el digito verificador y formatear.

El RUT se guarda normalizado sin puntos y con guion (`76123456-K`), que es la
forma que piden el SII y los proveedores de facturacion.
"""
import re


def clean(value):
    """'76.123.456-k' -> '76123456K'. No valida."""
    return re.sub(r'[^0-9kK]', '', value or '').upper()


def check_digit(body):
    """Digito verificador (modulo 11) del cuerpo numerico del RUT."""
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    rest = 11 - total % 11
    return {11: '0', 10: 'K'}.get(rest, str(rest))


def normalize(value):
    """RUT valido como '76123456-K', o None si no es un RUT valido."""
    rut = clean(value)
    if len(rut) < 2:
        return None
    body, dv = rut[:-1], rut[-1]
    if not body.isdigit() or not 1 <= len(body) <= 8:
        return None
    if check_digit(body) != dv:
        return None
    return f'{int(body)}-{dv}'


def pretty(rut):
    """'76123456-K' -> '76.123.456-K', para mostrar."""
    body, dv = rut.split('-')
    return f'{int(body):,}'.replace(',', '.') + f'-{dv}'

"""Formato de los datos que van dentro de un aviso."""


def clp(amount):
    """Entero CLP como se escribe en Chile: 29500 -> '29.500'.

    El dinero viaja en entero (ver AGENTS.md); esto es solo presentacion y no
    debe usarse para volver a parsear el monto.
    """
    return f'{int(amount or 0):,}'.replace(',', '.')

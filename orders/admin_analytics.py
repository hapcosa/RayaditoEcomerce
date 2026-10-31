"""Cruces de ventas para la app admin. Montado en /api/admin/analytics/.

Un solo endpoint arma cualquier combinacion de **tiempo x dimension**:

    ?from=2026-01-01&to=2026-03-31   rango por dia local, ambos incluidos
    &interval=day|week|month|total   como se corta el tiempo
    &dimension=none|catalog|category|product|region|shipping|attribute:<slug>
    &compare=previous|year|none      periodo contra el que comparar
    &limit=8                         cuantas claves mostrar; el resto va a "Otros"

La respuesta es "tidy": `rows` trae solo los cruces con ventas y `periods` /
`keys` dicen como armar el eje y la leyenda, asi el cliente rellena los ceros.

Reglas que conviene tener presentes:

* Misma definicion de venta que `admin_stats`: `paid_at` puesto y no
  cancelada/rechazada.
* Todo sale de `OrderItem`, con la foto del momento de la compra
  (`orders.snapshots`): `revenue_clp` es lo que pago el cliente por las piezas,
  sin el envio. El envio solo aparece en `totals`, porque no es de ninguna pieza.
* El margen solo se puede calcular donde hay costo. `revenue_without_cost_clp`
  dice cuanta venta quedo fuera, para no presentar un margen inflado.
* Con `attribute:<slug>`, una pieza con dos valores (agata y cuarzo) cuenta en
  los dos: las filas pueden sumar mas que el total.
* Dinero en entero CLP en toda la respuesta.
"""
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.db.models import Count, F, IntegerField, Max, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncWeek
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from product.models import Attribute, AttributeKind

from .admin_stats import _paid_orders
from .countries import Countries
from .models import OrderItem, OrderItemAttribute

DEFAULT_DAYS = 30
MAX_RANGE_DAYS = 3 * 366
MAX_DAILY_DAYS = 400
DEFAULT_LIMIT = 8
MAX_LIMIT = 50
OTHER_KEY = '__other__'
EMPTY_KEY = ''

TRUNC = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth}
INTERVALS = (*TRUNC, 'total')
COMPARES = ('previous', 'year', 'none')

# Dimensiones fijas: campo de `OrderItem` por el que se agrupa.
DIMENSION_FIELDS = {
    'catalog': 'catalog',
    'category': 'category_name',
    'product': 'product_id',
    'region': 'order__region',
    'shipping': 'order__shipping_id__name',
}
DIMENSION_LABELS = {
    'none': 'Total',
    'catalog': 'Catálogo',
    'category': 'Categoría',
    'product': 'Pieza',
    'region': 'Región',
    'shipping': 'Envío',
}

_ZERO = Value(0, output_field=IntegerField())


class BadParam(Exception):
    pass


# --- parametros --------------------------------------------------------------

def _parse_date(raw, name):
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        raise BadParam(f'`{name}` debe ser una fecha AAAA-MM-DD.')


def _parse_params(params, today):
    to_date = _parse_date(params['to'], 'to') if params.get('to') else today
    if params.get('from'):
        from_date = _parse_date(params['from'], 'from')
    else:
        from_date = to_date - timedelta(days=DEFAULT_DAYS - 1)
    if from_date > to_date:
        raise BadParam('`from` no puede ser posterior a `to`.')
    span = (to_date - from_date).days + 1
    if span > MAX_RANGE_DAYS:
        raise BadParam('El rango máximo es de 3 años.')

    interval = params.get('interval', 'day')
    if interval not in INTERVALS:
        raise BadParam(f'`interval` debe ser uno de: {", ".join(INTERVALS)}.')
    if interval == 'day' and span > MAX_DAILY_DAYS:
        raise BadParam('Para más de 400 días usa `interval=week` o `month`.')

    compare = params.get('compare', 'previous')
    if compare not in COMPARES:
        raise BadParam(f'`compare` debe ser uno de: {", ".join(COMPARES)}.')

    dimension = params.get('dimension', 'none')
    attribute = None
    if dimension.startswith('attribute:'):
        attribute = Attribute.objects.filter(slug=dimension.split(':', 1)[1]).first()
        if attribute is None:
            raise BadParam('Ese atributo no existe.')
    elif dimension != 'none' and dimension not in DIMENSION_FIELDS:
        raise BadParam('Dimensión desconocida.')

    try:
        limit = int(params.get('limit', DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
    limit = max(1, min(limit, MAX_LIMIT))

    return from_date, to_date, interval, compare, dimension, attribute, limit


def _shift_year(day):
    try:
        return day.replace(year=day.year - 1)
    except ValueError:  # 29 de febrero
        return day.replace(year=day.year - 1, day=28)


def _compare_range(from_date, to_date, compare):
    if compare == 'previous':
        span = (to_date - from_date).days + 1
        return from_date - timedelta(days=span), from_date - timedelta(days=1)
    if compare == 'year':
        return _shift_year(from_date), _shift_year(to_date)
    return None


# --- consultas ---------------------------------------------------------------

def _items(from_date, to_date):
    """Items vendidos en el rango (por dia local de `paid_at`)."""
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(from_date, time.min), tz)
    end = timezone.make_aware(datetime.combine(to_date + timedelta(days=1), time.min), tz)
    orders = _paid_orders().filter(paid_at__gte=start, paid_at__lt=end)
    return OrderItem.objects.filter(order__in=orders)


def _metrics(prefix=''):
    """Agregados por pieza. `prefix` permite agregar desde `OrderItemAttribute`."""
    price, count, cost = F(f'{prefix}price'), F(f'{prefix}count'), F(f'{prefix}unit_cost')
    has_cost = Q(**{f'{prefix}unit_cost__isnull': False})
    money = {'output_field': IntegerField()}
    return {
        'revenue_clp': Coalesce(Sum(price * count, **money), _ZERO),
        'units': Coalesce(Sum(count), _ZERO),
        'orders': Count(f'{prefix}order', distinct=True),
        'cost_clp': Coalesce(Sum(cost * count, filter=has_cost, **money), _ZERO),
        'costed_revenue_clp': Coalesce(Sum(price * count, filter=has_cost, **money), _ZERO),
    }


def _finish(row):
    """Pasa de los agregados crudos a las metricas que ve el cliente."""
    revenue = row['revenue_clp']
    costed = row.pop('costed_revenue_clp')
    row['margin_clp'] = costed - row['cost_clp']
    row['revenue_without_cost_clp'] = revenue - costed
    return row


def _grouped(items, dimension, attribute, interval):
    """Filas `(period, key, label, metricas)` sin recortar a las top N."""
    tz = timezone.get_current_timezone()

    if attribute is not None:
        querysets = [
            # Piezas con el atributo: una fila por valor.
            (OrderItemAttribute.objects.filter(item__in=items, attribute_slug=attribute.slug),
             'value', None),
            # Piezas sin el atributo: un solo grupo "Sin dato".
            (items.exclude(attributes__attribute_slug=attribute.slug), None, None),
        ]
    else:
        field = DIMENSION_FIELDS.get(dimension)
        label = Max('name') if dimension == 'product' else None
        querysets = [(items, field, label)]

    rows = []
    for qs, key_field, label_expr in querysets:
        own_prefix = 'item__' if qs.model is OrderItemAttribute else ''
        group = []
        if interval != 'total':
            qs = qs.annotate(
                period=TRUNC[interval](f'{own_prefix}order__paid_at', tzinfo=tz),
            )
            group.append('period')
        if key_field:
            group.append(key_field)
        annotations = _metrics(own_prefix)
        if label_expr is not None:
            annotations['label'] = label_expr
        for row in qs.values(*group).annotate(**annotations).order_by():
            period = row.pop('period', None)
            key = row.pop(key_field, EMPTY_KEY) if key_field else EMPTY_KEY
            label = row.pop('label', None)
            if not row['units']:
                continue
            # Region '...' es el "sin elegir" del formulario de direccion.
            if key is None or (dimension == 'region' and key == Countries.cero):
                key = EMPTY_KEY
            rows.append({
                'period': period.date().isoformat() if period else None,
                'key': str(key),
                'label': label,
                **_finish(row),
            })
    return rows


def _label(dimension, attribute, key, fallback=None):
    if key == OTHER_KEY:
        return 'Otros'
    if key == EMPTY_KEY:
        if dimension == 'none':
            return 'Total'
        name = attribute.name if attribute else DIMENSION_LABELS[dimension]
        return f'Sin {name.lower()}'
    if dimension == 'catalog':
        for catalog in settings.STORE.get('catalogs', []):
            if catalog['slug'] == key:
                return catalog['label']
    # Region: el valor guardado ya es el nombre legible ('Los Lagos'); la
    # etiqueta de `Countries` es el nombre del miembro ('Catorce').
    return fallback or key


def _merge(rows, keep, dimension, attribute):
    """Junta las claves fuera de `keep` en "Otros" y suma por (periodo, clave)."""
    merged = {}
    labels = {}
    for row in rows:
        key = row['key'] if row['key'] in keep else OTHER_KEY
        labels.setdefault(key, row['label'])
        bucket = merged.setdefault((row['period'], key), {
            'period': row['period'], 'key': key,
            'revenue_clp': 0, 'units': 0, 'orders': 0, 'cost_clp': 0,
            'margin_clp': 0, 'revenue_without_cost_clp': 0,
        })
        for metric in ('revenue_clp', 'units', 'orders', 'cost_clp',
                       'margin_clp', 'revenue_without_cost_clp'):
            bucket[metric] += row[metric]
    out = []
    for (period, key), bucket in sorted(
        merged.items(), key=lambda kv: (kv[0][0] or '', -kv[1]['revenue_clp']),
    ):
        bucket['label'] = _label(dimension, attribute, key, labels.get(key))
        out.append(bucket)
    return out


def _key_totals(rows):
    totals = {}
    for row in rows:
        bucket = totals.setdefault(row['key'], {'key': row['key'], 'label': row['label'],
                                                'revenue_clp': 0, 'units': 0})
        bucket['revenue_clp'] += row['revenue_clp']
        bucket['units'] += row['units']
    return totals


def _periods(from_date, to_date, interval):
    """Inicio de cada tramo del eje, en orden, incluyendo los vacios."""
    if interval == 'total':
        return []
    if interval == 'day':
        start, step = from_date, None
    elif interval == 'week':
        start, step = from_date - timedelta(days=from_date.weekday()), None
    else:
        start, step = from_date.replace(day=1), 'month'
    periods = []
    day = start
    while day <= to_date:
        periods.append(day.isoformat())
        if step == 'month':
            day = (day.replace(day=28) + timedelta(days=4)).replace(day=1)
        else:
            day += timedelta(days=7 if interval == 'week' else 1)
    return periods


def _totals(items):
    """Totales del rango, con el envio y el bruto que ve MercadoPago."""
    row = _finish(items.aggregate(**_metrics()))
    orders = _paid_orders().filter(pk__in=items.values('order'))
    shipping = orders.aggregate(total=Coalesce(Sum('shipping_price'), _ZERO))['total']
    row['shipping_clp'] = shipping
    row['gross_clp'] = row['revenue_clp'] + shipping
    # Division entera: el CLP no tiene decimales.
    row['average_order_clp'] = row['revenue_clp'] // row['orders'] if row['orders'] else 0
    return row


def _available_dimensions():
    fixed = [{'id': key, 'label': label} for key, label in DIMENSION_LABELS.items()]
    attributes = [
        {'id': f'attribute:{attr.slug}', 'label': attr.name}
        for attr in Attribute.objects.filter(kind=AttributeKind.SELECT)
    ]
    return fixed + attributes


class AdminAnalyticsView(APIView):
    """Ventas cruzadas por tiempo y dimension para la pestaña Ventas de la app."""
    permission_classes = (IsAdminUser,)

    def get(self, request):
        today = timezone.localdate()
        try:
            (from_date, to_date, interval, compare,
             dimension, attribute, limit) = _parse_params(request.query_params, today)
        except BadParam as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        items = _items(from_date, to_date)
        raw = _grouped(items, dimension, attribute, interval)

        # Las top N se eligen por venta en todo el rango, no tramo a tramo: si
        # no, la leyenda cambiaria de una barra a otra.
        totals_by_key = _key_totals(raw)
        ranked = sorted(totals_by_key.values(), key=lambda k: (-k['revenue_clp'], k['key']))
        keep = {k['key'] for k in ranked[:limit]}
        rows = _merge(raw, keep, dimension, attribute)

        keys = {}
        for row in _merge(
            [{**r, 'period': None} for r in raw], keep, dimension, attribute,
        ):
            keys[row['key']] = {key: row[key] for key in (
                'key', 'label', 'revenue_clp', 'units', 'orders', 'margin_clp',
            )}

        compare_block = None
        compare_range = _compare_range(from_date, to_date, compare)
        if compare_range:
            c_from, c_to = compare_range
            c_items = _items(c_from, c_to)
            c_raw = _grouped(c_items, dimension, attribute, 'total')
            c_keys = _merge(c_raw, keep, dimension, attribute)
            compare_block = {
                'from': c_from.isoformat(),
                'to': c_to.isoformat(),
                'totals': _totals(c_items),
                'keys': [{key: row[key] for key in ('key', 'label', 'revenue_clp', 'units')}
                         for row in c_keys],
            }

        return Response({
            'generated_at': timezone.now().isoformat(),
            'params': {
                'from': from_date.isoformat(),
                'to': to_date.isoformat(),
                'interval': interval,
                'dimension': dimension,
                'compare': compare,
                'limit': limit,
            },
            'totals': _totals(items),
            'periods': _periods(from_date, to_date, interval),
            'keys': sorted(keys.values(), key=lambda k: (k['key'] == OTHER_KEY,
                                                          -k['revenue_clp'])),
            'rows': rows,
            'compare': compare_block,
            'available_dimensions': _available_dimensions(),
        })

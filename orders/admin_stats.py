"""Metricas de venta para el panel del dueno. Montado en /api/admin/stats/.

Alimenta dos consumidores: el panel web (`/panel`, graficos con Recharts) y las
tarjetas numericas del home de la app admin. Por eso la respuesta trae tanto
totales sueltos como una serie diaria: cada cliente toma lo que le sirve en una
sola llamada.

Reglas del dominio que conviene tener presentes al leer esto:

* **No existe un estado "pagado".** `Order.status` es operativo (lo mueve el
  staff). Lo unico que dice que entro plata es `paid_at`, que escribe
  `payment.services.record_payment` en la primera aprobacion de MercadoPago.
* **`Order.amount` incluye el envio** (ver `payment/views.py`). Reportarlo a
  secas infla las ventas con lo que se lleva Starken, asi que se expone el
  bruto, el envio y el neto por separado.
* Dinero en entero CLP en toda la respuesta. El formateo es del cliente.
"""
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db.models import Count, F, IntegerField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from product.models import Product

from .models import Order, OrderItem

S = Order.OrderStatus

# Una venta cancelada o rechazada despues de haberse pagado no es una venta: el
# dueno quiere saber cuanto vendio, no cuanto cobro y devolvio.
VOID_STATUSES = (S.cancelled, S.refused)

DEFAULT_DAYS = 30
MAX_DAYS = 365
TOP_PRODUCTS_LIMIT = 5

# `amount` es nullable en el modelo (una orden recien creada puede no tenerlo),
# asi que toda suma de dinero pasa por Coalesce para no devolver null.
_ZERO = Value(0, output_field=IntegerField())


def _paid_orders():
    """Ordenes que representan plata efectivamente entrada y no revertida."""
    return Order.objects.filter(paid_at__isnull=False).exclude(status__in=VOID_STATUSES)


def _parse_days(raw):
    try:
        days = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_DAYS
    return max(1, min(days, MAX_DAYS))


def _totals(orders):
    """Totales de dinero y volumen sobre un queryset de ordenes pagadas."""
    money = orders.aggregate(
        orders_paid=Count('id'),
        gross_clp=Coalesce(Sum('amount'), _ZERO),
        shipping_clp=Coalesce(Sum('shipping_price'), _ZERO),
    )
    items = OrderItem.objects.filter(order__in=orders).aggregate(
        items_sold=Coalesce(Sum('count'), _ZERO),
    )
    gross = money['gross_clp']
    shipping = money['shipping_clp']
    count = money['orders_paid']
    return {
        'orders_paid': count,
        'gross_clp': gross,
        'shipping_clp': shipping,
        'net_clp': gross - shipping,
        'items_sold': items['items_sold'],
        # Division entera: el CLP no tiene decimales.
        'average_order_clp': gross // count if count else 0,
    }


def _series(orders, start_date, end_date):
    """Serie diaria con los dias vacios rellenos en cero.

    Recharts dibuja mal una serie con huecos: un dia sin ventas tiene que
    aparecer como cero, no desaparecer del eje.
    """
    tz = timezone.get_current_timezone()
    rows = (
        orders
        .annotate(day=TruncDate('paid_at', tzinfo=tz))
        .values('day')
        .annotate(
            orders=Count('id'),
            gross_clp=Coalesce(Sum('amount'), _ZERO),
            shipping_clp=Coalesce(Sum('shipping_price'), _ZERO),
        )
    )
    by_day = {
        row['day']: {
            'orders': row['orders'],
            'gross_clp': row['gross_clp'],
            'net_clp': row['gross_clp'] - row['shipping_clp'],
        }
        for row in rows
    }

    # Las unidades salen de otra tabla; se agrupan aparte y se pegan por fecha.
    item_rows = (
        OrderItem.objects.filter(order__in=orders)
        .annotate(day=TruncDate('order__paid_at', tzinfo=tz))
        .values('day')
        .annotate(items=Coalesce(Sum('count'), _ZERO))
    )
    items_by_day = {row['day']: row['items'] for row in item_rows}

    series = []
    day = start_date
    while day <= end_date:
        bucket = by_day.get(day)
        series.append({
            'date': day.isoformat(),
            'orders': bucket['orders'] if bucket else 0,
            'gross_clp': bucket['gross_clp'] if bucket else 0,
            'net_clp': bucket['net_clp'] if bucket else 0,
            'items': items_by_day.get(day, 0),
        })
        day += timedelta(days=1)
    return series


def _top_products(orders):
    """Los mas vendidos por plata neta, con el precio historico del pedido."""
    rows = (
        OrderItem.objects.filter(order__in=orders)
        .values('product_id', 'name')
        .annotate(
            units=Coalesce(Sum('count'), _ZERO),
            net_clp=Coalesce(Sum(F('price') * F('count'), output_field=IntegerField()), _ZERO),
        )
        .order_by('-net_clp', 'name')[:TOP_PRODUCTS_LIMIT]
    )
    return [
        {
            'product_id': row['product_id'],
            'name': row['name'],
            'units': row['units'],
            'net_clp': row['net_clp'],
        }
        for row in rows
    ]


def _pending(now):
    """Pedidos pagados que siguen sin salir, con el reloj de despacho encima.

    Mismo criterio que `notifications.services.orders_to_warn`, pero contando en
    vez de notificando: aca interesa el estado actual, no si ya se aviso.
    """
    pending = Order.objects.filter(
        status=S.processed, paid_at__isnull=False, shipped_at__isnull=True,
    )
    sla = timedelta(hours=settings.DISPATCH_SLA_HOURS)
    warn_margin = sla - timedelta(hours=settings.DISPATCH_WARN_HOURS)
    oldest = pending.order_by('paid_at').values_list('paid_at', flat=True).first()
    return {
        'awaiting_dispatch': pending.count(),
        # "Por vencer" excluye a los ya vencidos, que se cuentan aparte.
        'due_soon': pending.filter(
            paid_at__lte=now - warn_margin, paid_at__gt=now - sla,
        ).count(),
        'overdue': pending.filter(paid_at__lte=now - sla).count(),
        'oldest_paid_at': oldest.isoformat() if oldest else None,
    }


def _by_status():
    counts = {
        row['status']: row['total']
        for row in Order.objects.values('status').annotate(total=Count('id'))
    }
    return {str(value): counts.get(value, 0) for value in S.values}


def _catalog():
    """Piezas publicadas disponibles vs. agotadas (mismo criterio que la tienda)."""
    published = Product.objects.filter(status=Product.ProductStatus.PUBLISHED)
    return {
        'available': published.available().count(),
        'sold': published.sold_out().count(),
    }


class AdminStatsView(APIView):
    """Resumen de ventas para el panel web y el home de la app admin."""
    permission_classes = (IsAdminUser,)

    def get(self, request):
        days = _parse_days(request.query_params.get('days'))
        now = timezone.now()
        tz = timezone.get_current_timezone()

        # El rango se corta por dia local (incluye el dia de hoy completo), no
        # por "hace N*24 horas": el dueno piensa en dias de calendario.
        end_date = timezone.localtime(now, tz).date()
        start_date = end_date - timedelta(days=days - 1)
        start = timezone.make_aware(datetime.combine(start_date, time.min), tz)

        previous_start_date = start_date - timedelta(days=days)
        previous_start = start - timedelta(days=days)

        paid = _paid_orders()
        current = paid.filter(paid_at__gte=start, paid_at__lte=now)
        previous = paid.filter(paid_at__gte=previous_start, paid_at__lt=start)

        return Response({
            'generated_at': now.isoformat(),
            'period': {
                'days': days,
                'from': start_date.isoformat(),
                'to': end_date.isoformat(),
            },
            'totals': _totals(current),
            'previous': {
                'from': previous_start_date.isoformat(),
                'to': (start_date - timedelta(days=1)).isoformat(),
                **_totals(previous),
            },
            'pending': _pending(now),
            'series': _series(current, start_date, end_date),
            'top_products': _top_products(current),
            'by_status': _by_status(),
            'catalog': _catalog(),
        })

"""Tests de /api/admin/stats/ (resumen de ventas para el panel y la app admin).

Toca dinero, asi que cada total se verifica contra numeros calculados a mano.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from orders.models import Order, OrderItem
from product.models import Product

User = get_user_model()
S = Order.OrderStatus
URL = '/api/admin/stats/'


class AdminStatsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@rayadito.cl', password='Testpass123',
            first_name='Admin', last_name='Rayadito',
        )
        self.customer = User.objects.create_user(
            email='ana@rayadito.cl', password='Testpass123',
            first_name='Ana', last_name='Rios',
        )
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')
        self.anillo = Product.objects.create(
            name='Anillo de plata', product_type='joya', description='Hecho a mano',
            price=25000, compare_price=0, category=self.category, photo='',
        )
        self.colgante = Product.objects.create(
            name='Colgante de agata', product_type='joya', description='Hecho a mano',
            price=18000, compare_price=0, category=self.category, photo='',
        )
        self.now = timezone.now()

    def _paid_order(self, *, amount, shipping_price, days_ago, status_=S.shipping,
                    items=()):
        order = Order.objects.create(
            email='ana@cliente.cl', amount=amount, shipping_price=shipping_price,
            status=status_,
        )
        # `paid_at` no es auto_now_add: se puede fijar sin trucos de reloj.
        order.paid_at = self.now - timedelta(days=days_ago)
        order.save(update_fields=['paid_at'])
        for product, price, count in items:
            OrderItem.objects.create(
                order=order, product=product, name=product.name,
                price=price, count=count,
            )
        return order

    def _get(self, **params):
        self.client.force_authenticate(self.admin)
        res = self.client.get(URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return res.data

    # --- permisos ---
    def test_requires_authentication(self):
        res = self.client.get(URL)
        self.assertIn(res.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_requires_staff(self):
        self.client.force_authenticate(self.customer)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- dinero ---
    def test_totals_split_shipping_out_of_revenue(self):
        self._paid_order(amount=29500, shipping_price=4500, days_ago=1,
                         items=[(self.anillo, 25000, 1)])
        self._paid_order(amount=40500, shipping_price=4500, days_ago=2,
                         items=[(self.colgante, 18000, 2)])

        totals = self._get()['totals']
        self.assertEqual(totals['orders_paid'], 2)
        self.assertEqual(totals['gross_clp'], 70000)
        self.assertEqual(totals['shipping_clp'], 9000)
        self.assertEqual(totals['net_clp'], 61000)
        self.assertEqual(totals['items_sold'], 3)
        self.assertEqual(totals['average_order_clp'], 35000)

    def test_totals_are_zero_without_sales(self):
        totals = self._get()['totals']
        self.assertEqual(totals['orders_paid'], 0)
        self.assertEqual(totals['gross_clp'], 0)
        self.assertEqual(totals['net_clp'], 0)
        self.assertEqual(totals['average_order_clp'], 0)

    def test_unpaid_orders_do_not_count(self):
        Order.objects.create(amount=99000, shipping_price=4500)  # sin paid_at
        self.assertEqual(self._get()['totals']['orders_paid'], 0)

    def test_cancelled_and_refused_sales_are_excluded(self):
        self._paid_order(amount=29500, shipping_price=4500, days_ago=1)
        self._paid_order(amount=50000, shipping_price=0, days_ago=1,
                         status_=S.cancelled)
        self._paid_order(amount=60000, shipping_price=0, days_ago=1,
                         status_=S.refused)

        totals = self._get()['totals']
        self.assertEqual(totals['orders_paid'], 1)
        self.assertEqual(totals['gross_clp'], 29500)

    def test_average_order_uses_integer_clp(self):
        self._paid_order(amount=10000, shipping_price=0, days_ago=1)
        self._paid_order(amount=10001, shipping_price=0, days_ago=1)
        # 20001 / 2 = 10000.5 -> el CLP no tiene decimales.
        self.assertEqual(self._get()['totals']['average_order_clp'], 10000)

    # --- rango y comparacion ---
    def test_period_window_excludes_older_sales(self):
        self._paid_order(amount=10000, shipping_price=0, days_ago=2)
        self._paid_order(amount=90000, shipping_price=0, days_ago=40)

        data = self._get()
        self.assertEqual(data['period']['days'], 30)
        self.assertEqual(data['totals']['gross_clp'], 10000)

    def test_previous_period_covers_the_window_right_before(self):
        self._paid_order(amount=10000, shipping_price=0, days_ago=1)
        self._paid_order(amount=70000, shipping_price=0, days_ago=10)

        data = self._get(days=7)
        self.assertEqual(data['totals']['gross_clp'], 10000)
        self.assertEqual(data['previous']['gross_clp'], 70000)

    def test_days_param_is_clamped(self):
        self.assertEqual(self._get(days=0)['period']['days'], 1)
        self.assertEqual(self._get(days=9999)['period']['days'], 365)
        self.assertEqual(self._get(days='mucho')['period']['days'], 30)

    # --- serie ---
    def test_series_fills_empty_days_with_zero(self):
        self._paid_order(amount=29500, shipping_price=4500, days_ago=1,
                         items=[(self.anillo, 25000, 1)])

        series = self._get(days=7)['series']
        self.assertEqual(len(series), 7)
        self.assertEqual([row['date'] for row in series],
                         sorted(row['date'] for row in series))

        sold_day = (timezone.localtime(self.now) - timedelta(days=1)).date().isoformat()
        day = next(row for row in series if row['date'] == sold_day)
        self.assertEqual(day['orders'], 1)
        self.assertEqual(day['gross_clp'], 29500)
        self.assertEqual(day['net_clp'], 25000)
        self.assertEqual(day['items'], 1)

        empty = [row for row in series if row['date'] != sold_day]
        self.assertTrue(all(row['orders'] == 0 and row['gross_clp'] == 0
                            and row['items'] == 0 for row in empty))

    # --- top de productos ---
    def test_top_products_uses_historic_item_prices(self):
        self._paid_order(amount=50000, shipping_price=0, days_ago=1,
                         items=[(self.anillo, 20000, 1), (self.colgante, 15000, 2)])
        # El precio del catalogo cambia despues de la venta: el reporte no.
        self.colgante.price = 99000
        self.colgante.save(update_fields=['price'])

        top = self._get()['top_products']
        self.assertEqual(top[0]['name'], 'Colgante de agata')
        self.assertEqual(top[0]['units'], 2)
        self.assertEqual(top[0]['net_clp'], 30000)
        self.assertEqual(top[1]['net_clp'], 20000)

    # --- pendientes de despacho ---
    @override_settings(DISPATCH_SLA_HOURS=72, DISPATCH_WARN_HOURS=24)
    def test_pending_splits_due_soon_from_overdue(self):
        fresh = self._paid_order(amount=10000, shipping_price=0, days_ago=0,
                                 status_=S.processed)
        due_soon = self._paid_order(amount=10000, shipping_price=0, days_ago=2,
                                    status_=S.processed)
        overdue = self._paid_order(amount=10000, shipping_price=0, days_ago=5,
                                   status_=S.processed)

        pending = self._get()['pending']
        self.assertEqual(pending['awaiting_dispatch'], 3)
        self.assertEqual(pending['due_soon'], 1)
        self.assertEqual(pending['overdue'], 1)
        self.assertTrue(pending['oldest_paid_at'].startswith(
            overdue.paid_at.date().isoformat()))
        self.assertIsNotNone(fresh.paid_at)
        self.assertIsNotNone(due_soon.paid_at)

    def test_dispatched_orders_are_not_pending(self):
        order = self._paid_order(amount=10000, shipping_price=0, days_ago=5,
                                 status_=S.processed)
        order.shipped_at = self.now
        order.save(update_fields=['shipped_at'])

        pending = self._get()['pending']
        self.assertEqual(pending['awaiting_dispatch'], 0)
        self.assertIsNone(pending['oldest_paid_at'])

    # --- catalogo y estados ---
    def test_catalog_counts_published_pieces_by_stock(self):
        self.anillo.stock = 0
        self.anillo.save(update_fields=['stock'])
        Product.objects.create(
            name='Borrador', product_type='joya', description='No publicado',
            price=1000, compare_price=0, category=self.category, photo='',
            status=Product.ProductStatus.DRAFT,
        )

        catalog = self._get()['catalog']
        self.assertEqual(catalog['sold'], 1)
        self.assertEqual(catalog['available'], 1)

    def test_by_status_lists_every_status(self):
        self._paid_order(amount=10000, shipping_price=0, days_ago=1,
                         status_=S.processed)
        by_status = self._get()['by_status']
        self.assertEqual(set(by_status), {str(v) for v in S.values})
        self.assertEqual(by_status[str(S.processed)], 1)
        self.assertEqual(by_status[str(S.refused)], 0)

    def test_by_status_ignores_the_period_window(self):
        # `by_status` es la foto operativa de hoy: un pedido viejo sin despachar
        # sigue siendo trabajo pendiente aunque quede fuera del rango.
        self._paid_order(amount=10000, shipping_price=0, days_ago=200,
                         status_=S.processed)
        data = self._get(days=7)
        self.assertEqual(data['totals']['orders_paid'], 0)
        self.assertEqual(data['by_status'][str(S.processed)], 1)

"""Tests de /api/admin/analytics/, de la foto de la venta y del borrado protegido.

Toca dinero, asi que cada total se verifica contra numeros calculados a mano.
"""
from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from orders.models import Order, OrderItem
from payment.services import create_order_item
from product.models import Attribute, AttributeValue, Product, ProductAttributeValue

User = get_user_model()
S = Order.OrderStatus
URL = '/api/admin/analytics/'


def at(day):
    """Mediodia local del dia dado: lejos de cualquier borde de zona horaria."""
    return timezone.make_aware(datetime.combine(day, time(12)))


class AnalyticsBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@rayadito.cl', password='Testpass123',
            first_name='Admin', last_name='Rayadito',
        )
        self.anillos = Category.objects.create(name='Anillos', ProductType='Joya')
        self.colgantes = Category.objects.create(name='Colgantes', ProductType='Joya')
        self.piedra = Attribute.objects.create(name='Piedra', slug='piedra')
        self.agata = AttributeValue.objects.create(attribute=self.piedra, value='Ágata')
        self.cuarzo = AttributeValue.objects.create(attribute=self.piedra, value='Cuarzo')

        self.anillo = self._product('Anillo de ágata', 25000, self.anillos, cost=10000,
                                    values=[self.agata])
        self.colgante = self._product('Colgante doble', 18000, self.colgantes,
                                      values=[self.agata, self.cuarzo])
        self.aro = self._product('Aro simple', 9000, self.anillos, cost=4000)

    def _product(self, name, price, category, cost=None, values=()):
        product = Product.objects.create(
            name=name, product_type='joya', description='Hecho a mano', price=price,
            compare_price=0, category=category, photo='', cost=cost,
        )
        for value in values:
            ProductAttributeValue.objects.create(product=product, attribute_value=value)
        return product

    def _sale(self, day, products, shipping=0, status_=S.shipping, region='Metropolitana'):
        """Venta pagada el `day`, creada por el mismo camino que el checkout."""
        order = Order.objects.create(
            email='ana@cliente.cl', shipping_price=shipping, status=status_,
            region=region,
        )
        for product in products:
            create_order_item(order, product, 1)
        order.amount = sum(p.price for p in products) + shipping
        order.paid_at = at(day)
        order.save(update_fields=['amount', 'paid_at'])
        return order

    def _get(self, expected=status.HTTP_200_OK, **params):
        self.client.force_authenticate(self.admin)
        res = self.client.get(URL, params)
        self.assertEqual(res.status_code, expected, res.content)
        return res.data


class SnapshotTests(AnalyticsBase):
    def test_la_venta_guarda_categoria_catalogo_costo_y_atributos(self):
        order = self._sale(date(2026, 3, 10), [self.colgante])
        item = order.orderitem_set.get()

        self.assertEqual(item.category_name, 'Colgantes')
        self.assertEqual(item.catalog, 'joya')
        self.assertIsNone(item.unit_cost)
        self.assertEqual(
            sorted(item.attributes.values_list('value', flat=True)), ['Cuarzo', 'Ágata'],
        )

    def test_reclasificar_la_pieza_no_reescribe_lo_vendido(self):
        self._sale(date(2026, 3, 10), [self.anillo])
        self.anillo.category = self.colgantes
        self.anillo.cost = 99999
        self.anillo.save()

        data = self._get(**{'from': '2026-03-01', 'to': '2026-03-31',
                            'interval': 'total', 'dimension': 'category'})

        self.assertEqual([k['label'] for k in data['keys']], ['Anillos'])
        self.assertEqual(data['totals']['cost_clp'], 10000)


class ProductDeleteTests(AnalyticsBase):
    def test_una_pieza_vendida_no_se_puede_borrar(self):
        self._sale(date(2026, 3, 10), [self.anillo])
        self.client.force_authenticate(self.admin)

        res = self.client.delete(f'/api/admin/products/{self.anillo.pk}/')

        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Product.objects.filter(pk=self.anillo.pk).exists())

    def test_una_pieza_sin_ventas_se_borra(self):
        self.client.force_authenticate(self.admin)

        res = self.client.delete(f'/api/admin/products/{self.aro.pk}/')

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_el_costo_se_edita_desde_la_api_admin(self):
        self.client.force_authenticate(self.admin)

        res = self.client.patch(f'/api/admin/products/{self.aro.pk}/', {'cost': 3500},
                                format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content)
        self.assertEqual(res.data['cost'], 3500)


class AnalyticsApiTests(AnalyticsBase):
    def test_requiere_staff(self):
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)
        cliente = User.objects.create_user(email='c@rayadito.cl', password='Testpass123')
        self.client.force_authenticate(cliente)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_403_FORBIDDEN)

    def test_totales_separan_envio_y_calculan_margen_solo_con_costo(self):
        self._sale(date(2026, 3, 10), [self.anillo, self.colgante], shipping=4500)
        self._sale(date(2026, 3, 12), [self.aro])

        totals = self._get(**{'from': '2026-03-01', 'to': '2026-03-31'})['totals']

        self.assertEqual(totals['revenue_clp'], 25000 + 18000 + 9000)
        self.assertEqual(totals['shipping_clp'], 4500)
        self.assertEqual(totals['gross_clp'], 52000 + 4500)
        self.assertEqual(totals['orders'], 2)
        self.assertEqual(totals['units'], 3)
        self.assertEqual(totals['average_order_clp'], 52000 // 2)
        # Costo conocido: anillo 10.000 + aro 4.000. El colgante no tiene.
        self.assertEqual(totals['cost_clp'], 14000)
        self.assertEqual(totals['margin_clp'], (25000 + 9000) - 14000)
        self.assertEqual(totals['revenue_without_cost_clp'], 18000)

    def test_canceladas_y_no_pagadas_no_cuentan(self):
        self._sale(date(2026, 3, 10), [self.anillo], status_=S.cancelled)
        Order.objects.create(email='x@x.cl', amount=9000)  # nunca pagada

        totals = self._get(**{'from': '2026-03-01', 'to': '2026-03-31'})['totals']

        self.assertEqual(totals['revenue_clp'], 0)
        self.assertEqual(totals['orders'], 0)

    def test_serie_mensual_con_todos_los_meses_en_el_eje(self):
        self._sale(date(2026, 1, 15), [self.anillo])
        self._sale(date(2026, 3, 2), [self.aro])

        data = self._get(**{'from': '2026-01-01', 'to': '2026-03-31', 'interval': 'month'})

        self.assertEqual(data['periods'], ['2026-01-01', '2026-02-01', '2026-03-01'])
        by_period = {r['period']: r['revenue_clp'] for r in data['rows']}
        self.assertEqual(by_period, {'2026-01-01': 25000, '2026-03-01': 9000})

    def test_semana_empieza_el_lunes(self):
        # 2026-03-04 es miercoles: su semana empieza el lunes 2026-03-02.
        self._sale(date(2026, 3, 4), [self.aro])

        data = self._get(**{'from': '2026-03-04', 'to': '2026-03-10', 'interval': 'week'})

        self.assertEqual(data['periods'], ['2026-03-02', '2026-03-09'])
        self.assertEqual(data['rows'][0]['period'], '2026-03-02')

    def test_cruce_tiempo_por_categoria(self):
        self._sale(date(2026, 1, 15), [self.anillo, self.colgante])
        self._sale(date(2026, 2, 3), [self.aro])

        data = self._get(**{'from': '2026-01-01', 'to': '2026-02-28',
                            'interval': 'month', 'dimension': 'category'})

        cells = {(r['period'], r['label']): r['revenue_clp'] for r in data['rows']}
        self.assertEqual(cells, {
            ('2026-01-01', 'Anillos'): 25000,
            ('2026-01-01', 'Colgantes'): 18000,
            ('2026-02-01', 'Anillos'): 9000,
        })
        self.assertEqual([k['label'] for k in data['keys']], ['Anillos', 'Colgantes'])

    def test_atributo_con_varios_valores_cuenta_en_cada_uno(self):
        self._sale(date(2026, 3, 10), [self.anillo, self.colgante, self.aro])

        data = self._get(**{'from': '2026-03-01', 'to': '2026-03-31',
                            'interval': 'total', 'dimension': 'attribute:piedra'})

        keys = {k['label']: k['revenue_clp'] for k in data['keys']}
        self.assertEqual(keys, {
            'Ágata': 25000 + 18000,
            'Cuarzo': 18000,
            'Sin piedra': 9000,  # el aro no tiene piedra
        })

    def test_region_y_catalogo_usan_etiquetas_legibles(self):
        self._sale(date(2026, 3, 10), [self.aro], region='Los Lagos')
        self._sale(date(2026, 3, 11), [self.aro], region='...')

        region = self._get(**{'from': '2026-03-01', 'to': '2026-03-31',
                              'interval': 'total', 'dimension': 'region'})
        catalog = self._get(**{'from': '2026-03-01', 'to': '2026-03-31',
                               'interval': 'total', 'dimension': 'catalog'})

        self.assertEqual(sorted(k['label'] for k in region['keys']),
                         ['Los Lagos', 'Sin región'])
        self.assertEqual([k['label'] for k in catalog['keys']], ['Joyas'])

    def test_lo_que_pasa_del_limite_va_a_otros(self):
        self._sale(date(2026, 3, 10), [self.anillo, self.colgante, self.aro])

        data = self._get(**{'from': '2026-03-01', 'to': '2026-03-31',
                            'interval': 'total', 'dimension': 'product', 'limit': 1})

        keys = [(k['label'], k['revenue_clp']) for k in data['keys']]
        self.assertEqual(keys, [('Anillo de ágata', 25000), ('Otros', 18000 + 9000)])

    def test_compara_con_el_periodo_anterior_y_el_anio_anterior(self):
        self._sale(date(2026, 3, 10), [self.anillo])
        self._sale(date(2026, 2, 10), [self.aro])
        self._sale(date(2025, 3, 10), [self.colgante])

        previous = self._get(**{'from': '2026-03-01', 'to': '2026-03-31'})['compare']
        year = self._get(**{'from': '2026-03-01', 'to': '2026-03-31',
                            'compare': 'year'})['compare']

        self.assertEqual((previous['from'], previous['to']), ('2026-01-29', '2026-02-28'))
        self.assertEqual(previous['totals']['revenue_clp'], 9000)
        self.assertEqual((year['from'], year['to']), ('2025-03-01', '2025-03-31'))
        self.assertEqual(year['totals']['revenue_clp'], 18000)

    def test_dimensiones_disponibles_incluyen_atributos(self):
        ids = [d['id'] for d in self._get()['available_dimensions']]
        self.assertIn('category', ids)
        self.assertIn('attribute:piedra', ids)

    def test_parametros_invalidos_dan_400(self):
        for params in (
            {'from': '2026-03-31', 'to': '2026-03-01'},
            {'from': 'ayer'},
            {'interval': 'hora'},
            {'dimension': 'color'},
            {'dimension': 'attribute:no-existe'},
            {'from': '2020-01-01', 'to': '2026-01-01', 'interval': 'month'},
            {'from': '2025-01-01', 'to': '2026-03-01', 'interval': 'day'},
        ):
            with self.subTest(params=params):
                self._get(expected=status.HTTP_400_BAD_REQUEST, **params)

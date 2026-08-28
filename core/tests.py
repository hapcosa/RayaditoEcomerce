"""Tests del ruteo raiz del proyecto.

Fijan el cutover a Next.js: Django dejo de servir la tienda y ya no tiene el
catch-all que devolvia el `index.html` del SPA de Vite para cualquier ruta.
"""
from django.test import TestCase


class RootRoutingTests(TestCase):
    def test_unknown_route_returns_json_404_not_the_spa(self):
        # Antes del cutover esto devolvia 200 con el HTML del SPA, que se comia
        # cualquier URL equivocada y ocultaba errores de ruteo del proxy.
        res = self.client.get('/una-ruta-que-no-existe')

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res['Content-Type'], 'application/json')
        self.assertIn('error', res.json())

    def test_storefront_root_is_not_served_by_django(self):
        # La portada la sirve Next.js; el proxy nunca deberia mandar `/` aca.
        res = self.client.get('/')

        self.assertEqual(res.status_code, 404)

    def test_api_routes_still_resolve(self):
        res = self.client.get('/api/products/')

        self.assertEqual(res.status_code, 200)

    def test_media_is_served_with_debug_off(self):
        # Regresion del cutover: la media se servia con `static()`, que solo
        # actua con DEBUG=True. Sin el SPA y sin nginx delante, en produccion
        # las fotos de producto quedaban en 404.
        from django.conf import settings
        from django.urls import resolve

        match = resolve(f'{settings.MEDIA_URL}photos/26/08/x.jpg')

        self.assertEqual(match.func.__name__, 'serve')
        self.assertEqual(
            match.kwargs['document_root'], settings.MEDIA_ROOT)

    def test_admin_still_resolves(self):
        res = self.client.get('/admin/login/')

        self.assertEqual(res.status_code, 200)

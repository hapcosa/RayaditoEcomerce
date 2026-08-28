"""El buzon publico tiene freno; el webhook de pagos no."""
from django.core.cache import cache
from rest_framework import status
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase


class SuggestionThrottleTests(APITestCase):
    def setUp(self):
        # El throttle guarda el historial en cache: sin limpiarlo, el conteo se
        # arrastra entre tests.
        cache.clear()

    def _post(self, n):
        return self.client.post('/api/suggestions/create', {
            'name': 'Ana', 'email': f'ana{n}@rayadito.cl', 'message': 'Hola!',
        }, format='json')

    def test_public_suggestion_form_is_rate_limited(self):
        # Formulario abierto sin auth: sin freno es un buzon de spam.
        rate = api_settings.DEFAULT_THROTTLE_RATES['suggestions']
        allowed = int(rate.split('/')[0])

        for n in range(allowed):
            self.assertEqual(self._post(n).status_code,
                             status.HTTP_201_CREATED, f'peticion {n}')

        blocked = self._post(allowed)

        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_payment_webhook_is_not_throttled(self):
        # Lo llama MercadoPago y reintenta: frenarlo perderia confirmaciones.
        from payment.views import MercadoPagoResponse

        self.assertEqual(MercadoPagoResponse.throttle_classes, ())

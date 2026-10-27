"""Test runner que fija una tienda de prueba conocida.

Los tests prueban el código, no la configuración de una tienda concreta: con
este runner corren igual en Rayadito y en cualquier fork, sea cual sea su
store.json. `core/test_store.json` trae dos catálogos ('joya' y 'piedra') con
textos ficticios. El store.json real del repo lo valida `core.test_store`.
"""
import os

from django.conf import settings
from django.test.runner import DiscoverRunner

from core.store import load_store

TEST_STORE_PATH = os.path.join(os.path.dirname(__file__), 'test_store.json')


class StoreTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        settings.STORE = load_store(TEST_STORE_PATH)

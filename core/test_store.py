"""Configuración de la tienda (store.json) y lo que depende de ella."""
import copy
import io
import json
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APITestCase

from category.models import Category
from core.store import load_store, validate_store
from core.test_runner import TEST_STORE_PATH

User = get_user_model()

TEXTIL = validate_store({
    'slug': 'textil',
    'name': 'Tienda Textil',
    'short_name': 'Textil',
    'description': 'Ropa tejida a mano.',
    'domain': 'textil.test',
    'catalogs': [{
        'slug': 'ropa', 'path': 'ropa', 'label': 'Ropa', 'singular': 'Prenda',
        'category_type': 'Ropa',
    }],
})


def store_with(**changes):
    data = json.loads(open(TEST_STORE_PATH, encoding='utf-8').read())
    data.update(changes)
    return data


class RepoStoreFileTests(SimpleTestCase):
    def test_repo_store_json_is_valid(self):
        # El store.json real de este repo (Rayadito o un fork) tiene que cargar.
        store = load_store(os.path.join(settings.BASE_DIR, 'store.json'))

        self.assertTrue(store['catalogs'])


class ValidateStoreTests(SimpleTestCase):
    def assertInvalid(self, data, fragment):
        with self.assertRaisesMessage(ImproperlyConfigured, fragment):
            validate_store(data)

    def test_fills_optional_texts(self):
        minimal = copy.deepcopy(TEXTIL)

        self.assertEqual(minimal['tagline'], '')
        self.assertEqual(minimal['email_from_name'], 'Tienda Textil')
        self.assertEqual(minimal['catalogs'][0]['description'], '')

    def test_requires_brand_texts(self):
        self.assertInvalid(store_with(name=''), '"name"')

    def test_requires_at_least_one_catalog(self):
        self.assertInvalid(store_with(catalogs=[]), '"catalogs"')

    def test_rejects_bad_slugs(self):
        catalogs = store_with()['catalogs']
        catalogs[0]['path'] = 'Joyas Finas'
        self.assertInvalid(store_with(catalogs=catalogs), 'catalogs[0].path')

    def test_rejects_reserved_general(self):
        catalogs = store_with()['catalogs']
        catalogs[0]['slug'] = 'general'
        self.assertInvalid(store_with(catalogs=catalogs), 'reservado')

    def test_rejects_duplicated_paths(self):
        catalogs = store_with()['catalogs']
        catalogs[1]['path'] = catalogs[0]['path']
        self.assertInvalid(store_with(catalogs=catalogs), 'repetido')

    def test_reports_missing_file_and_bad_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesMessage(ImproperlyConfigured, 'no existe'):
                load_store(os.path.join(tmp, 'store.json'))
            broken = os.path.join(tmp, 'roto.json')
            with open(broken, 'w', encoding='utf-8') as f:
                f.write('{"name": ')
            with self.assertRaisesMessage(ImproperlyConfigured, 'JSON inválido'):
                load_store(broken)


class StoreConfigEndpointTests(APITestCase):
    def test_exposes_brand_and_catalogs(self):
        res = self.client.get('/api/store/')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['name'], 'Tienda de Prueba')
        self.assertEqual([c['path'] for c in res.json()['catalogs']], ['joyas', 'piedras'])

    @override_settings(STORE=TEXTIL)
    def test_follows_the_configured_store(self):
        res = self.client.get('/api/store/')

        self.assertEqual(res.json()['catalogs'][0]['slug'], 'ropa')


class CatalogCategoriesTests(APITestCase):
    def setUp(self):
        Category.objects.create(name='Anillos', ProductType='Joya')
        Category.objects.create(name='Chalecos', ProductType='Ropa')

    def test_lists_the_catalog_categories_by_path(self):
        res = self.client.get('/api/category/catalog/joyas')

        self.assertEqual(res.status_code, 200)
        self.assertEqual([c['name'] for c in res.json()['categories']], ['Anillos'])

    def test_unknown_catalog_is_404(self):
        res = self.client.get('/api/category/catalog/ropa')

        self.assertEqual(res.status_code, 404)

    @override_settings(STORE=TEXTIL)
    def test_other_store_catalogs(self):
        res = self.client.get('/api/category/catalog/ropa')

        self.assertEqual([c['name'] for c in res.json()['categories']], ['Chalecos'])


_MEDIA_ROOT = tempfile.mkdtemp(prefix='store-test-media-')


def _image_file():
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (4, 4), (120, 90, 60)).save(buf, format='PNG')
    return SimpleUploadedFile('foto.png', buf.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=_MEDIA_ROOT)
class AdminProductTypeTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.staff = User.objects.create_user(
            email='staff@example.com', password='x', first_name='S', last_name='T',
            is_staff=True,
        )
        self.client.force_authenticate(self.staff)
        self.category = Category.objects.create(name='Chalecos', ProductType='Ropa')

    def create(self, product_type):
        return self.client.post('/api/admin/products/', {
            'name': 'Chaleco de lana', 'description': 'x', 'price': 30000,
            'category': self.category.id, 'product_type': product_type,
            'photo': _image_file(),
        }, format='multipart')

    @override_settings(STORE=TEXTIL)
    def test_accepts_the_store_catalogs(self):
        res = self.create('ropa')

        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()['product_type'], 'ropa')

    @override_settings(STORE=TEXTIL)
    def test_rejects_catalogs_of_another_store(self):
        res = self.create('joya')

        self.assertEqual(res.status_code, 400)
        self.assertIn('product_type', res.json())


class BrandedEmailTests(TestCase):
    def test_customer_mail_uses_the_store_brand(self):
        from notifications.services import send_customer_mail

        send_customer_mail(
            'cliente@example.com', 'Retracto', 'notifications/customer_withdrawal_received.txt',
            {'withdrawal': None, 'reference': '1', 'order': None},
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Tienda de Prueba — firma de los tests', mail.outbox[0].body)

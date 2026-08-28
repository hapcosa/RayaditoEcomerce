"""Tests de la API de escritura staff (/api/admin/products/). Fase 5."""
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category
from product.models import GalleryProduct, Product

User = get_user_model()

# MEDIA_ROOT temporal: los uploads de estos tests no deben ensuciar public/.
_MEDIA_ROOT = tempfile.mkdtemp(prefix='rayadito-test-media-')


def _png_bytes():
    """PNG válido mínimo en memoria (Pillow ya es dependencia por ImageField)."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (4, 4), (120, 90, 60)).save(buf, format='PNG')
    return buf.getvalue()


def _image_file(name='foto.png'):
    return SimpleUploadedFile(name, _png_bytes(), content_type='image/png')


@override_settings(MEDIA_ROOT=_MEDIA_ROOT)
class AdminProductApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.staff = User.objects.create_user(
            email='dueno@rayadito.cl', password='Testpass123',
            first_name='Due', last_name='Ño', is_staff=True,
        )
        self.customer = User.objects.create_user(
            email='cliente@rayadito.cl', password='Testpass123',
            first_name='Cli', last_name='Ente',
        )
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')

    def _create_payload(self, **overrides):
        payload = {
            'name': 'Anillo ágata',
            'description': 'Plata y ágata de Chiloé',
            'price': 25000,
            'compare_price': 0,
            'category': self.category.id,
            'product_type': 'joya',
            'status': Product.ProductStatus.PUBLISHED,
            'photo': _image_file(),
        }
        payload.update(overrides)
        return payload

    # --- permisos ---
    def test_create_requires_staff(self):
        self.client.force_authenticate(self.customer)
        res = self.client.post('/api/admin/products/', self._create_payload(),
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_requires_auth(self):
        res = self.client.post('/api/admin/products/', self._create_payload(),
                               format='multipart')
        self.assertIn(res.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # --- creación / dinero CLP ---
    def test_staff_creates_product_with_int_clp_price(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/admin/products/', self._create_payload(),
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        product = Product.objects.get(id=res.data['id'])
        self.assertEqual(product.price, 25000)
        self.assertIsInstance(res.data['price'], int)
        self.assertTrue(product.slug)  # slug autogenerado

    def test_create_requires_product_type(self):
        # Sin product_type el producto quedaria 'general' e invisible en ambos
        # catalogos publicos: la API lo rechaza antes de crearlo.
        self.client.force_authenticate(self.staff)
        payload = self._create_payload()
        del payload['product_type']
        res = self.client.post('/api/admin/products/', payload,
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_type', res.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_rejects_unclassified_product_type(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/admin/products/',
                               self._create_payload(product_type='general'),
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_type', res.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_created_product_is_listed_in_its_public_catalog(self):
        # Regresion: los productos creados por la app admin no aparecian en
        # ningun catalogo publico porque quedaban con product_type 'general'.
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/admin/products/',
                               self._create_payload(product_type='piedra'),
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

        self.client.force_authenticate(None)
        listed = self.client.get('/api/products/', {'product_type': 'piedra'})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual([p['id'] for p in listed.data['products']],
                         [res.data['id']])

        otro = self.client.get('/api/products/', {'product_type': 'joya'})
        self.assertEqual(otro.data['products'], [])

    def test_rejects_decimal_price(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/admin/products/',
                               self._create_payload(price='1000.5'),
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_negative_price(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post('/api/admin/products/',
                               self._create_payload(price=-5),
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # --- edición ---
    def test_staff_updates_price(self):
        self.client.force_authenticate(self.staff)
        created = self.client.post('/api/admin/products/', self._create_payload(),
                                   format='multipart')
        pid = created.data['id']
        res = self.client.patch(f'/api/admin/products/{pid}/',
                                {'price': 30000}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Product.objects.get(id=pid).price, 30000)

    # --- galería (multipart) ---
    def test_staff_uploads_gallery_images(self):
        self.client.force_authenticate(self.staff)
        created = self.client.post('/api/admin/products/', self._create_payload(),
                                   format='multipart')
        pid = created.data['id']
        res = self.client.post(
            f'/api/admin/products/{pid}/images/',
            {'images': [_image_file('a.png'), _image_file('b.png')]},
            format='multipart',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(len(res.data['gallery']), 2)
        self.assertEqual(GalleryProduct.objects.filter(product_id=pid).count(), 2)

    def test_gallery_upload_without_files_is_400(self):
        self.client.force_authenticate(self.staff)
        created = self.client.post('/api/admin/products/', self._create_payload(),
                                   format='multipart')
        pid = created.data['id']
        res = self.client.post(f'/api/admin/products/{pid}/images/', {},
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_gallery_upload_requires_staff(self):
        self.client.force_authenticate(self.staff)
        created = self.client.post('/api/admin/products/', self._create_payload(),
                                   format='multipart')
        pid = created.data['id']
        self.client.force_authenticate(self.customer)
        res = self.client.post(
            f'/api/admin/products/{pid}/images/',
            {'images': [_image_file()]}, format='multipart',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- categorías (picker de la app) ---
    def test_staff_lists_all_categories_flat(self):
        Category.objects.create(name='Colgantes', ProductType='Joya')
        Category.objects.create(name='Ágatas', ProductType='Piedra')
        self.client.force_authenticate(self.staff)
        res = self.client.get('/api/admin/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Sin filtrar por ProductType: las tres categorías (setUp + 2) vienen.
        names = {c['name'] for c in res.data}
        self.assertEqual(names, {'Anillos', 'Colgantes', 'Ágatas'})

    def test_categories_list_requires_staff(self):
        self.client.force_authenticate(self.customer)
        res = self.client.get('/api/admin/categories/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

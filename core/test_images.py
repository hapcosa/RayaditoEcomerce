"""Tests del achicado de fotos (subidas nuevas y el comando para las viejas)."""
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from category.models import Category
from core.images import MAX_SIDE
from homepage.models import HeroImage
from product.models import GalleryProduct, Product

MEDIA_TEMPORAL = tempfile.mkdtemp(prefix='rayadito-test-images-')


def jpeg(width, height, name='foto.jpg', orientation=None):
    buffer = io.BytesIO()
    image = Image.new('RGB', (width, height), (218, 95, 21))
    if orientation:
        exif = Image.Exif()
        exif[0x0112] = orientation
        image.save(buffer, format='JPEG', exif=exif)
    else:
        image.save(buffer, format='JPEG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/jpeg')


def size_of(field_file):
    with field_file.open('rb') as handle:
        return Image.open(handle).size


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class ShrinkTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.category = Category.objects.create(name='Anillos', ProductType='Joya')

    def _product(self, photo):
        return Product.objects.create(
            name='Anillo', product_type='joya', description='x', price=1000,
            category=self.category, photo=photo,
        )

    def test_una_foto_grande_se_achica_al_subir(self):
        product = self._product(jpeg(4000, 3000))
        self.assertEqual(size_of(product.photo), (MAX_SIDE, 1920))

    def test_una_foto_chica_queda_igual(self):
        product = self._product(jpeg(800, 600))
        self.assertEqual(size_of(product.photo), (800, 600))

    def test_galeria_y_portada_tambien_se_achican(self):
        product = self._product(jpeg(800, 600))
        gallery = GalleryProduct.objects.create(product=product, photos=jpeg(3000, 6000))
        hero = HeroImage.objects.create(image=jpeg(9248, 4164))
        self.assertEqual(max(size_of(gallery.photos)), MAX_SIDE)
        self.assertEqual(max(size_of(hero.image)), MAX_SIDE)

    def test_respeta_la_orientacion_del_celular(self):
        # Orientacion 6 = la camara guardo la foto acostada: hay que girarla.
        product = self._product(jpeg(4000, 3000, orientation=6))
        self.assertEqual(size_of(product.photo), (1920, MAX_SIDE))

    def test_editar_el_producto_no_reprocesa_la_foto(self):
        product = self._product(jpeg(4000, 3000))
        name = product.photo.name
        product.name = 'Anillo de plata'
        product.save()
        self.assertEqual(product.photo.name, name)

    def test_el_comando_achica_las_viejas_sin_cambiar_el_nombre(self):
        product = self._product(jpeg(800, 600))
        # Simula una foto vieja subida antes del achicado: se pisa en disco.
        with open(product.photo.path, 'wb') as handle:
            Image.new('RGB', (5000, 2500)).save(handle, format='JPEG')
        name = product.photo.name

        call_command('shrink_photos', '--dry-run', stdout=io.StringIO())
        self.assertEqual(size_of(product.photo), (5000, 2500))

        call_command('shrink_photos', stdout=io.StringIO())
        product.refresh_from_db()
        self.assertEqual(product.photo.name, name)
        self.assertEqual(size_of(product.photo), (MAX_SIDE, 1280))

        out = io.StringIO()
        call_command('shrink_photos', stdout=out)  # idempotente
        self.assertIn('0 foto(s) achicadas', out.getvalue())

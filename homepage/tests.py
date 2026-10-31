"""Tests de la portada: limite de fotos activas, orden y permisos de staff."""
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from .models import HeroImage, HomepageSettings, hero_max_photos

User = get_user_model()

# Las fotos de los tests van a un directorio temporal: con el MEDIA_ROOT real
# cada corrida dejaba archivos basura dentro del repo.
MEDIA_TEMPORAL = tempfile.mkdtemp(prefix='rayadito-test-media-')
media_temporal = override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)


class MediaTemporalMixin:
    """Aisla `MEDIA_ROOT` y lo borra al terminar la clase de tests."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)
        super().tearDownClass()

HERO_LIST = '/api/homepage/hero'
ADMIN_LIST = '/api/admin/hero-images/'


def foto(nombre='portada.jpg'):
    """JPEG minimo real: `ImageField` valida el contenido, no basta un bytes."""
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), (218, 95, 21)).save(buffer, format='JPEG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/jpeg')


@media_temporal
class HeroImageModelTests(MediaTemporalMixin, TestCase):
    def test_no_deja_activar_mas_fotos_que_el_tope(self):
        for i in range(hero_max_photos()):
            HeroImage.objects.create(image=foto(f'{i}.jpg'), position=i)

        cuarta = HeroImage(image=foto('cuarta.jpg'))
        with self.assertRaises(ValidationError):
            cuarta.clean()

    def test_una_foto_activa_puede_seguir_editandose(self):
        """Editar una activa no debe contarse a si misma como una cuarta."""
        for i in range(hero_max_photos()):
            hero = HeroImage.objects.create(image=foto(f'{i}.jpg'), position=i)

        hero.caption = 'Ágata de Cucao'
        hero.clean()  # no debe levantar

    def test_desactivar_libera_el_cupo(self):
        fotos = [
            HeroImage.objects.create(image=foto(f'{i}.jpg'), position=i)
            for i in range(hero_max_photos())
        ]
        fotos[0].is_active = False
        fotos[0].save()

        HeroImage(image=foto('nueva.jpg')).clean()  # no debe levantar


@media_temporal
class HeroImagePublicAPITests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_devuelve_solo_las_activas_y_en_orden(self):
        HeroImage.objects.create(image=foto('b.jpg'), position=2, alt_text='b')
        HeroImage.objects.create(image=foto('a.jpg'), position=1, alt_text='a')
        HeroImage.objects.create(
            image=foto('off.jpg'), position=0, alt_text='off', is_active=False,
        )

        res = self.client.get(HERO_LIST)

        self.assertEqual(res.status_code, 200)
        self.assertEqual([f['alt_text'] for f in res.json()], ['a', 'b'])

    def test_sin_fotos_devuelve_lista_vacia(self):
        """La portada tiene que seguir funcionando antes de la primera subida."""
        res = self.client.get(HERO_LIST)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), [])


@media_temporal
class HeroImageAdminAPITests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            email='staff@rayadito.cl', password='clave-larga-1', is_staff=True,
        )
        self.cliente = User.objects.create_user(
            email='cliente@rayadito.cl', password='clave-larga-2',
        )

    def test_un_cliente_no_puede_tocar_la_portada(self):
        self.client.force_authenticate(self.cliente)

        self.assertEqual(self.client.get(ADMIN_LIST).status_code, 403)
        self.assertEqual(
            self.client.post(ADMIN_LIST, {'image': foto()}, format='multipart').status_code,
            403,
        )

    def test_anonimo_no_puede_tocar_la_portada(self):
        self.assertEqual(self.client.get(ADMIN_LIST).status_code, 401)

    def test_staff_sube_una_foto(self):
        self.client.force_authenticate(self.staff)

        res = self.client.post(
            ADMIN_LIST,
            {'image': foto(), 'alt_text': 'Ágata rayada', 'position': 1},
            format='multipart',
        )

        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(HeroImage.objects.count(), 1)
        self.assertEqual(HeroImage.objects.get().alt_text, 'Ágata rayada')

    def test_pasar_el_tope_con_is_active_da_400_y_no_500(self):
        for i in range(hero_max_photos()):
            HeroImage.objects.create(image=foto(f'{i}.jpg'), position=i)
        self.client.force_authenticate(self.staff)

        res = self.client.post(
            ADMIN_LIST, {'image': foto(), 'is_active': 'true'}, format='multipart',
        )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(HeroImage.objects.count(), hero_max_photos())

    def test_con_la_portada_llena_la_foto_nueva_queda_archivada(self):
        """Subir no depende de sacar antes otra foto: la nueva espera archivada."""
        for i in range(hero_max_photos()):
            HeroImage.objects.create(image=foto(f'{i}.jpg'), position=i)
        self.client.force_authenticate(self.staff)

        res = self.client.post(ADMIN_LIST, {'image': foto()}, format='multipart')

        self.assertEqual(res.status_code, 201, res.content)
        self.assertFalse(res.json()['is_active'])
        self.assertEqual(
            HeroImage.objects.filter(is_active=True).count(), hero_max_photos(),
        )

    def test_una_foto_subida_por_multipart_nace_activa(self):
        """Regresion: DRF lee un booleano ausente en multipart como `False`.

        La app sube la foto sin mandar `is_active`, asi que nacia desactivada y
        la portada no cambiaba nunca.
        """
        self.client.force_authenticate(self.staff)

        res = self.client.post(ADMIN_LIST, {'image': foto()}, format='multipart')

        self.assertEqual(res.status_code, 201, res.content)
        self.assertTrue(res.json()['is_active'])

    def test_staff_lista_activas_e_inactivas(self):
        HeroImage.objects.create(image=foto('on.jpg'))
        HeroImage.objects.create(image=foto('off.jpg'), is_active=False)
        self.client.force_authenticate(self.staff)

        res = self.client.get(ADMIN_LIST)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 2)

    def test_staff_borra_una_foto(self):
        hero = HeroImage.objects.create(image=foto())
        self.client.force_authenticate(self.staff)

        res = self.client.delete(f'{ADMIN_LIST}{hero.pk}/')

        self.assertEqual(res.status_code, 204)
        self.assertFalse(HeroImage.objects.exists())


@media_temporal
class HeroImageMedidasTests(MediaTemporalMixin, TestCase):
    """El sitio dibuja cada foto con su proporción: necesita las medidas."""

    def test_la_api_publica_devuelve_ancho_y_alto(self):
        HeroImage.objects.create(image=foto('medidas.jpg'))
        res = APIClient().get(HERO_LIST)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data[0]['width'], 8)
        self.assertEqual(res.data[0]['height'], 8)

    def test_una_foto_sin_archivo_no_voltea_la_portada(self):
        hero = HeroImage.objects.create(image=foto('borrada.jpg'))
        hero.image.storage.delete(hero.image.name)
        res = APIClient().get(HERO_LIST)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.data[0]['width'])
        self.assertIsNone(res.data[0]['height'])


@media_temporal
class HomepageSettingsTests(MediaTemporalMixin, TestCase):
    """La dueña elige cuántas fotos muestra la portada (entre 3 y 7)."""

    URL = '/api/admin/homepage-settings/'

    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            email='staff@rayadito.cl', password='clave-larga-1', is_staff=True,
        )

    def _fotos(self, n):
        return [
            HeroImage.objects.create(image=foto(f'{i}.jpg'), position=i, alt_text=str(i))
            for i in range(n)
        ]

    def test_por_defecto_son_cinco_y_viajan_los_topes(self):
        self.client.force_authenticate(self.staff)

        res = self.client.get(self.URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {
            'hero_max_photos': 5, 'min_hero_photos': 3, 'max_hero_photos': 7,
        })

    def test_staff_sube_el_tope_y_puede_activar_mas(self):
        self.client.force_authenticate(self.staff)
        self._fotos(5)

        res = self.client.patch(self.URL, {'hero_max_photos': 7}, format='json')

        self.assertEqual(res.status_code, 200, res.content)
        HeroImage(image=foto('sexta.jpg')).clean()  # ya no levanta

    def test_fuera_de_rango_da_400(self):
        self.client.force_authenticate(self.staff)
        for valor in (2, 8):
            with self.subTest(valor=valor):
                res = self.client.patch(self.URL, {'hero_max_photos': valor}, format='json')
                self.assertEqual(res.status_code, 400)
        self.assertEqual(hero_max_photos(), 5)

    def test_bajar_el_tope_archiva_las_ultimas_sin_borrarlas(self):
        self.client.force_authenticate(self.staff)
        self._fotos(5)

        res = self.client.patch(self.URL, {'hero_max_photos': 3}, format='json')

        self.assertEqual(res.status_code, 200, res.content)
        activas = HeroImage.objects.filter(is_active=True).values_list('alt_text', flat=True)
        self.assertEqual(list(activas), ['0', '1', '2'])
        self.assertEqual(HeroImage.objects.count(), 5)

    def test_crear_el_ajuste_no_archiva_nada(self):
        """El primer `load()` crea la fila: no debe tocar una portada ya armada."""
        self._fotos(6)  # mas que el default, p. ej. cargadas desde el admin
        HomepageSettings.load()
        self.assertEqual(HeroImage.objects.filter(is_active=True).count(), 6)

    def test_la_api_publica_respeta_el_tope(self):
        self._fotos(5)
        HomepageSettings.objects.update_or_create(pk=1, defaults={'hero_max_photos': 7})
        HeroImage.objects.create(image=foto('6.jpg'), position=6, alt_text='6')

        res = APIClient().get(HERO_LIST)

        self.assertEqual(len(res.json()), 6)

    def test_un_cliente_no_cambia_el_tope(self):
        cliente = User.objects.create_user(email='c@rayadito.cl', password='clave-larga-2')
        self.client.force_authenticate(cliente)
        res = self.client.patch(self.URL, {'hero_max_photos': 7}, format='json')
        self.assertEqual(res.status_code, 403)

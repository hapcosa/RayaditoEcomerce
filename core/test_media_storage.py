"""Storage de la media: configuracion por env y copia al bucket."""
import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from core import media_storage


def fake_env(values):
    """Imita `environ.Env.__call__`: sin default, una variable faltante revienta."""
    missing = object()

    def env(name, default=missing):
        if name in values:
            return values[name]
        if default is missing:
            raise KeyError(name)
        return default
    return env


R2_ENV = {
    'AWS_STORAGE_BUCKET_NAME': 'rayadito-media',
    'AWS_ACCESS_KEY_ID': 'id',
    'AWS_SECRET_ACCESS_KEY': 'secret',
    'AWS_S3_ENDPOINT_URL': 'https://abc123.r2.cloudflarestorage.com',
    'AWS_S3_CUSTOM_DOMAIN': 'media.example.cl',
}


class MediaStorageConfigTests(SimpleTestCase):
    def test_local_is_the_default(self):
        config = media_storage.media_storage_config('local', fake_env({}))

        self.assertEqual(config, media_storage.LOCAL)

    def test_s3_reads_the_public_domain(self):
        config = media_storage.media_storage_config('s3', fake_env(R2_ENV))

        self.assertEqual(config['BACKEND'], media_storage.S3_BACKEND)
        self.assertEqual(config['OPTIONS']['custom_domain'], 'media.example.cl')
        self.assertFalse(config['OPTIONS']['querystring_auth'])

    def test_custom_domain_is_optional_for_plain_s3(self):
        env = {k: v for k, v in R2_ENV.items()
               if k not in ('AWS_S3_CUSTOM_DOMAIN', 'AWS_S3_ENDPOINT_URL')}
        config = media_storage.media_storage_config('s3', fake_env(env))

        self.assertIsNone(config['OPTIONS']['custom_domain'])

    def test_photo_urls_use_the_public_domain(self):
        # Con boto3 instalado el backend real arma la URL sin tocar la red:
        # esta es la URL que la API le entrega a la tienda y a Instagram.
        from storages.backends.s3boto3 import S3Boto3Storage

        options = media_storage.media_storage_config('s3', fake_env(R2_ENV))['OPTIONS']
        storage = S3Boto3Storage(**options)

        self.assertEqual(
            storage.url('photos/26/08/anillo.jpg'),
            'https://media.example.cl/photos/26/08/anillo.jpg')

    def test_uploads_carry_cache_control(self):
        from storages.backends.s3boto3 import S3Boto3Storage

        options = media_storage.media_storage_config('s3', fake_env(R2_ENV))['OPTIONS']
        storage = S3Boto3Storage(**options)
        params = storage.get_object_parameters('photos/x.jpg')

        self.assertEqual(params['CacheControl'], media_storage.MEDIA_CACHE_CONTROL)


class CopyMediaToStorageTests(SimpleTestCase):
    def setUp(self):
        self.source = Path(tempfile.mkdtemp(prefix='rayadito-media-src-'))
        self.addCleanup(shutil.rmtree, self.source, ignore_errors=True)
        (self.source / 'photos' / '26' / '08').mkdir(parents=True)
        (self.source / 'photos' / '26' / '08' / 'anillo.jpg').write_bytes(b'jpg')
        (self.source / 'portada').mkdir()
        (self.source / 'portada' / 'hero.png').write_bytes(b'png')
        (self.source / '.DS_Store').write_bytes(b'basura')

        self.bucket = InMemoryStorage()
        patcher = mock.patch(
            'core.management.commands.copy_media_to_storage.default_storage',
            self.bucket)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_command(self, *args):
        out = StringIO()
        call_command('copy_media_to_storage', '--source', str(self.source), *args, stdout=out)
        return out.getvalue()

    def test_copies_files_with_the_same_key(self):
        self.run_command()

        self.assertTrue(self.bucket.exists('photos/26/08/anillo.jpg'))
        self.assertEqual(self.bucket.open('portada/hero.png').read(), b'png')
        self.assertFalse(self.bucket.exists('.DS_Store'))

    def test_is_idempotent(self):
        self.run_command()
        out = self.run_command()

        self.assertIn('0 archivo(s) subidos, 2 ya estaban', out)

    def test_skips_what_is_already_in_the_bucket(self):
        self.bucket.save('portada/hero.png', ContentFile(b'ya estaba'))

        out = self.run_command()

        self.assertIn('1 archivo(s) subidos, 1 ya estaban', out)
        self.assertEqual(self.bucket.open('portada/hero.png').read(), b'ya estaba')

    def test_dry_run_uploads_nothing(self):
        out = self.run_command('--dry-run')

        self.assertIn('subiria photos/26/08/anillo.jpg', out)
        self.assertFalse(self.bucket.exists('photos/26/08/anillo.jpg'))

    def test_refuses_to_copy_onto_itself(self):
        from django.core.files.storage import FileSystemStorage

        with mock.patch(
                'core.management.commands.copy_media_to_storage.default_storage',
                FileSystemStorage(location=str(self.source))):
            with self.assertRaises(CommandError):
                self.run_command()

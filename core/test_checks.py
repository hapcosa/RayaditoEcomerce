"""Los chequeos de despliegue avisan de configuracion incompleta."""
from unittest import mock

from django.test import SimpleTestCase, override_settings

from core import checks


@override_settings(DEBUG=False)
class DeployChecksTests(SimpleTestCase):
    @override_settings(EMAIL_BACKEND=checks.CONSOLE_EMAIL)
    def test_console_email_backend_is_an_error_in_production(self):
        found = checks.check_email_backend(None)

        self.assertEqual([e.id for e in found], ['rayadito.E001'])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_real_smtp_backend_passes(self):
        self.assertEqual(checks.check_email_backend(None), [])

    @mock.patch.dict('os.environ', {}, clear=True)
    def test_missing_mercadopago_token_is_an_error(self):
        found = checks.check_mercadopago_configured(None)

        self.assertEqual([e.id for e in found], ['rayadito.E002'])

    @mock.patch.dict('os.environ', {'MERCADOPAGO_ACCESS_TOKEN': 'x'})
    def test_configured_mercadopago_passes(self):
        self.assertEqual(checks.check_mercadopago_configured(None), [])

    @override_settings(STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}})
    def test_local_media_storage_warns(self):
        found = checks.check_media_storage(None)

        self.assertEqual([w.id for w in found], ['rayadito.W001'])

    @override_settings(STORAGES={
        'default': {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'}})
    def test_object_storage_passes(self):
        self.assertEqual(checks.check_media_storage(None), [])

    @override_settings(DEBUG=True, EMAIL_BACKEND=checks.CONSOLE_EMAIL)
    def test_checks_are_inert_in_development(self):
        # En dev el backend de consola es lo correcto y no debe molestar.
        self.assertEqual(checks.check_email_backend(None), [])


def _s3(**options):
    return {'default': {'BACKEND': checks.S3_STORAGE, 'OPTIONS': options}}


class ObjectStorageCheckTests(SimpleTestCase):
    @override_settings(STORAGES=_s3(
        endpoint_url='https://abc.r2.cloudflarestorage.com',
        custom_domain='media.example.cl'))
    def test_r2_with_public_domain_passes(self):
        self.assertEqual(checks.check_object_storage(None), [])

    @override_settings(STORAGES=_s3(
        endpoint_url='https://abc.r2.cloudflarestorage.com', custom_domain=None))
    def test_r2_without_public_domain_is_an_error(self):
        found = checks.check_object_storage(None)

        self.assertEqual([e.id for e in found], ['rayadito.E004'])

    @override_settings(STORAGES=_s3(endpoint_url=None, custom_domain=None))
    def test_plain_s3_does_not_need_custom_domain(self):
        self.assertEqual(checks.check_object_storage(None), [])

    @override_settings(DEBUG=True, STORAGES=_s3(
        endpoint_url='https://abc.r2.cloudflarestorage.com', custom_domain=None))
    def test_is_not_silenced_in_development(self):
        self.assertEqual(
            [e.id for e in checks.check_object_storage(None)], ['rayadito.E004'])

    @override_settings(STORAGES=_s3(
        endpoint_url='https://abc.r2.cloudflarestorage.com',
        custom_domain='media.example.cl'))
    def test_missing_boto3_is_an_error(self):
        with mock.patch.dict('sys.modules', {'boto3': None}):
            found = checks.check_object_storage(None)

        self.assertEqual([e.id for e in found], ['rayadito.E003'])

    @override_settings(STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}})
    def test_local_storage_is_ignored(self):
        self.assertEqual(checks.check_object_storage(None), [])

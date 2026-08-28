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

"""Token de Instagram en la base: cifrado, respaldo del .env y renovacion."""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from social import instagram, tokens
from social.models import InstagramToken

INSTAGRAM_LOGIN = override_settings(
    INSTAGRAM_USER_ID='17841400000000000',
    INSTAGRAM_ACCESS_TOKEN='',
    INSTAGRAM_GRAPH_HOST='graph.instagram.com',
)


def meta_response(payload):
    response = mock.Mock(status_code=200)
    response.json.return_value = payload
    return response


@INSTAGRAM_LOGIN
class TokenStorageTests(TestCase):
    def test_token_is_encrypted_at_rest(self):
        tokens.save_token('IGAA-secreto')

        row = InstagramToken.objects.get()
        self.assertNotIn('IGAA-secreto', row.encrypted_token)
        self.assertEqual(tokens.access_token(), 'IGAA-secreto')

    @override_settings(INSTAGRAM_ACCESS_TOKEN='del-env')
    def test_env_token_is_the_fallback_until_one_is_stored(self):
        self.assertEqual(tokens.access_token(), 'del-env')

        tokens.save_token('de-la-base')

        self.assertEqual(tokens.access_token(), 'de-la-base')

    def test_a_different_secret_key_cannot_read_it(self):
        tokens.save_token('IGAA-secreto')

        with override_settings(SECRET_KEY='otra-clave-' + 'x' * 40):
            self.assertEqual(tokens.access_token(), '')
            self.assertFalse(instagram.is_configured())

    def test_publishing_uses_the_stored_token(self):
        tokens.save_token('de-la-base')
        response = meta_response({'id': '1'})

        with mock.patch('social.instagram.requests.post', return_value=response) as post:
            instagram._request('POST', 'me/media', {'image_url': 'x'})

        self.assertEqual(post.call_args.kwargs['data']['access_token'], 'de-la-base')

    def test_errors_never_leak_the_stored_token(self):
        tokens.save_token('de-la-base')

        with mock.patch('social.instagram.requests.get',
                        side_effect=ConnectionError('url?access_token=de-la-base')):
            with self.assertRaises(instagram.InstagramError) as ctx:
                instagram._request('GET', 'me', {})

        self.assertNotIn('de-la-base', str(ctx.exception))


@INSTAGRAM_LOGIN
class TokenRefreshTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        tokens.save_token('viejo', expires_in=10 * 86400, now=self.now - timedelta(days=50))

    def test_refreshes_when_close_to_expiry(self):
        response = meta_response({'access_token': 'nuevo', 'token_type': 'bearer',
                                  'expires_in': 5183944})
        with mock.patch('social.tokens.requests.get', return_value=response) as get:
            self.assertTrue(tokens.refresh(now=self.now))

        params = get.call_args.kwargs['params']
        self.assertEqual(params, {'grant_type': 'ig_refresh_token', 'access_token': 'viejo'})
        self.assertEqual(get.call_args.args[0], 'https://graph.instagram.com/refresh_access_token')
        row = InstagramToken.objects.get()
        self.assertEqual(tokens.access_token(), 'nuevo')
        self.assertEqual(row.issued_at, self.now)
        self.assertEqual(row.expires_at, self.now + timedelta(seconds=5183944))
        self.assertEqual(row.last_refresh_attempt, self.now)

    def test_does_nothing_when_far_from_expiry(self):
        tokens.save_token('fresco', expires_in=55 * 86400, now=self.now - timedelta(days=5))

        with mock.patch('social.tokens.requests.get') as get:
            self.assertFalse(tokens.refresh(now=self.now))
        get.assert_not_called()

    def test_respects_metas_24_hour_minimum(self):
        tokens.save_token('recien', now=self.now - timedelta(hours=2))

        with mock.patch('social.tokens.requests.get') as get:
            self.assertFalse(tokens.refresh(now=self.now))
            with self.assertRaisesMessage(tokens.TokenError, '24 horas'):
                tokens.refresh(now=self.now, force=True)
        get.assert_not_called()

    def test_meta_error_is_recorded_and_the_old_token_kept(self):
        response = meta_response({'error': {'message': 'Session has expired', 'code': 190}})
        with mock.patch('social.tokens.requests.get', return_value=response):
            with self.assertRaisesMessage(tokens.TokenError, 'code 190'):
                tokens.refresh(now=self.now)

        row = InstagramToken.objects.get()
        self.assertIn('Session has expired', row.last_error)
        self.assertEqual(tokens.access_token(), 'viejo')

    def test_network_error_does_not_leak_the_token(self):
        with mock.patch('social.tokens.requests.get',
                        side_effect=ConnectionError('?access_token=viejo')):
            with self.assertRaises(tokens.TokenError) as ctx:
                tokens.refresh(now=self.now)

        self.assertNotIn('viejo', str(ctx.exception))
        self.assertNotIn('viejo', InstagramToken.objects.get().last_error)

    @override_settings(INSTAGRAM_GRAPH_HOST='graph.facebook.com')
    def test_system_user_tokens_are_not_refreshed(self):
        with mock.patch('social.tokens.requests.get') as get:
            self.assertFalse(tokens.refresh(now=self.now, force=True))
        get.assert_not_called()


@INSTAGRAM_LOGIN
class TokenCommandTests(TestCase):
    def run_command(self, *args, stdin=''):
        out = StringIO()
        with mock.patch('sys.stdin', StringIO(stdin)):
            call_command('instagram_token', *args, stdout=out)
        return out.getvalue()

    def test_set_reads_the_token_from_stdin(self):
        self.run_command('set', '--expires-in-days', '60', stdin='IGAA-pegado\n')

        self.assertEqual(tokens.access_token(), 'IGAA-pegado')
        self.assertIsNotNone(InstagramToken.objects.get().expires_at)

    @override_settings(INSTAGRAM_ACCESS_TOKEN='del-env')
    def test_set_from_env_migrates_the_old_token(self):
        out = self.run_command('set', '--from-env')

        self.assertIn('borrar INSTAGRAM_ACCESS_TOKEN', out)
        self.assertTrue(InstagramToken.objects.exists())

    def test_empty_token_is_rejected(self):
        with self.assertRaises(CommandError):
            self.run_command('set', stdin='\n')

    def test_status_never_prints_the_token(self):
        tokens.save_token('IGAA-secreto', expires_in=60 * 86400)

        out = self.run_command('status')

        self.assertIn('Vence:', out)
        self.assertNotIn('IGAA-secreto', out)

    def test_failed_refresh_pushes_an_alert_and_fails(self):
        tokens.save_token('viejo', now=timezone.now() - timedelta(days=59))
        response = meta_response({'error': {'message': 'expired', 'code': 190}})

        with mock.patch('social.tokens.requests.get', return_value=response), \
                mock.patch('notifications.services.push_admins') as push:
            with self.assertRaises(CommandError):
                self.run_command('refresh')

        push.assert_called_once()
        self.assertIn('Instagram', push.call_args.kwargs['title'])

    def test_refresh_without_a_stored_token_is_a_quiet_no_op(self):
        with mock.patch('notifications.services.push_admins') as push:
            out = self.run_command('refresh')

        self.assertIn('nada que renovar', out)
        push.assert_not_called()

"""Login social por djoser (`/auth/o/{provider}/`) con Google simulado.

Recorre el mismo flujo que `web/lib/auth.ts`: GET por la URL de autorización,
vuelta con `state` y `code` en la query, y JWT de respuesta. Google se simula
en la capa HTTP (`requests`), así el test pasa por el backend de
social-auth-core tal cual y detecta si una actualización rompe el contrato.
"""
import json
from unittest import mock
from urllib.parse import parse_qs, urlparse

import requests
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

User = get_user_model()

CALLBACK = 'http://localhost:3000/auth/social/callback'
GOOGLE_USER = {
    'sub': '108000000000000000001',
    'email': 'ana@example.com',
    'email_verified': True,
    'name': 'Ana Pérez',
    'given_name': 'Ana',
    'family_name': 'Pérez',
}


def fake_google(method, url, *args, **kwargs):
    if 'token' in url:
        payload = {'access_token': 'ya29.fake', 'token_type': 'Bearer', 'expires_in': 3600}
    elif 'userinfo' in url:
        payload = GOOGLE_USER
    else:
        raise AssertionError(f'Llamada HTTP inesperada: {method} {url}')
    response = requests.Response()
    response.status_code = 200
    response.url = url
    response.headers['Content-Type'] = 'application/json'
    response._content = json.dumps(payload).encode()
    return response


@override_settings(
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY='client-id.apps.googleusercontent.com',
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET='client-secret',
)
class GoogleSocialLoginTests(APITestCase):
    def start(self):
        res = self.client.get('/auth/o/google-oauth2/', {'redirect_uri': CALLBACK})
        self.assertEqual(res.status_code, 200, res.content)
        query = parse_qs(urlparse(res.json()['authorization_url']).query)
        self.assertEqual(query['redirect_uri'], [CALLBACK])
        return query['state'][0]

    def complete(self, state, code='4/fake-code'):
        with mock.patch.object(requests.Session, 'request', side_effect=fake_google):
            return self.client.post(
                f'/auth/o/google-oauth2/?state={state}&code={code}',
                content_type='application/x-www-form-urlencoded',
            )

    def test_authorization_url_points_to_google(self):
        res = self.client.get('/auth/o/google-oauth2/', {'redirect_uri': CALLBACK})

        self.assertTrue(
            res.json()['authorization_url'].startswith('https://accounts.google.com/'))

    def test_rejects_redirect_uri_not_allowed(self):
        res = self.client.get(
            '/auth/o/google-oauth2/', {'redirect_uri': 'https://evil.example/cb'})

        self.assertEqual(res.status_code, 400)

    def test_completes_login_and_returns_jwt(self):
        state = self.start()

        res = self.complete(state)

        self.assertEqual(res.status_code, 201, res.content)
        self.assertIn('access', res.json())
        self.assertIn('refresh', res.json())
        user = User.objects.get(email='ana@example.com')
        self.assertEqual(user.first_name, 'Ana')
        self.assertTrue(user.social_auth.filter(provider='google-oauth2').exists())

    def test_second_login_reuses_the_account(self):
        self.complete(self.start())
        self.client.cookies.clear()

        res = self.complete(self.start())

        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(User.objects.filter(email='ana@example.com').count(), 1)

    def test_rejects_tampered_state(self):
        self.start()

        res = self.complete('state-falso')

        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(email='ana@example.com').exists())

    def test_rejects_missing_state(self):
        self.start()

        with mock.patch.object(requests.Session, 'request', side_effect=fake_google):
            res = self.client.post(
                '/auth/o/google-oauth2/?code=4/fake-code',
                content_type='application/x-www-form-urlencoded',
            )

        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(email='ana@example.com').exists())

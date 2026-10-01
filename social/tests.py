"""Publicacion de productos en Instagram (API oficial, sin red en los tests)."""
import io
import shutil
import tempfile
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from category.models import Category
from product.models import GalleryProduct, Product
from social import instagram, services
from social.models import InstagramPost

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp(prefix='rayadito-social-tests-')

CONNECTED = override_settings(
    INSTAGRAM_USER_ID='17841400000000000',
    INSTAGRAM_ACCESS_TOKEN='secret-token',
    INSTAGRAM_GRAPH_HOST='graph.instagram.com',
    INSTAGRAM_GRAPH_VERSION='v23.0',
    INSTAGRAM_HASHTAGS=['#PiedrasRayadito', '#Chiloe'],
    FRONTEND_BASE_URL='https://piedrasdelrayadito.cl',
    BACKEND_BASE_URL='https://piedrasdelrayadito.cl',
    MEDIA_ROOT=MEDIA_ROOT,
)


def image_file(name='foto.png', size=(800, 800), fmt='PNG'):
    buffer = io.BytesIO()
    Image.new('RGBA' if fmt == 'PNG' else 'RGB', size, (120, 90, 60)).save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')


def tearDownModule():
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class ProductMixin:
    def make_product(self, **extra):
        category, _ = Category.objects.get_or_create(name='Anillos', ProductType='Joya')
        data = {
            'name': 'Anillo de ágata', 'product_type': 'joya',
            'description': '<p>Ágata de <b>Chiloé</b> engastada en plata.</p>',
            'price': 25000, 'compare_price': 0, 'category': category,
            'photo': image_file(),
        }
        data.update(extra)
        return Product.objects.create(**data)


@CONNECTED
class CaptionTests(ProductMixin, TestCase):
    def test_caption_has_name_plain_description_price_link_and_hashtags(self):
        product = self.make_product()
        caption = services.build_caption(product)
        self.assertTrue(caption.startswith('Anillo de ágata\n\n'))
        self.assertIn('Ágata de Chiloé engastada en plata.', caption)
        self.assertNotIn('<b>', caption)
        self.assertIn('$25.000', caption)
        self.assertIn(f'https://piedrasdelrayadito.cl/productos/{product.slug}', caption)
        self.assertTrue(caption.endswith('#PiedrasRayadito #Chiloe'))

    @override_settings(FRONTEND_BASE_URL='', INSTAGRAM_HASHTAGS=[])
    def test_caption_without_shop_url_or_hashtags(self):
        caption = services.build_caption(self.make_product())
        self.assertNotIn('Disponible en', caption)
        self.assertNotIn('#', caption)

    def test_caption_respects_instagram_limit(self):
        product = self.make_product(description='palabra ' * 2000)
        self.assertLessEqual(len(services.build_caption(product)),
                             services.CAPTION_MAX_CHARS)


@CONNECTED
class ImagePreparationTests(ProductMixin, TestCase):
    def jpeg_size(self, upload, **kwargs):
        product = self.make_product(photo=upload, **kwargs)
        data = services._to_instagram_jpeg(product.photo)
        image = Image.open(io.BytesIO(data))
        self.assertEqual(image.format, 'JPEG')
        return image.size

    def test_png_becomes_jpeg(self):
        self.assertEqual(self.jpeg_size(image_file()), (800, 800))

    def test_too_tall_photo_is_padded_to_4_5(self):
        width, height = self.jpeg_size(image_file(size=(400, 1000)))
        self.assertEqual(height, 1000)
        self.assertEqual(width, 800)

    def test_too_wide_photo_is_padded_to_191_1(self):
        width, height = self.jpeg_size(image_file(size=(1000, 200)))
        self.assertEqual(width, 1000)
        self.assertAlmostEqual(width / height, 1.91, places=2)

    def test_large_photo_is_scaled_down(self):
        width, _ = self.jpeg_size(image_file(size=(3000, 3000), fmt='JPEG'))
        self.assertEqual(width, services.MAX_WIDTH)

    def test_prepare_images_returns_public_urls_main_photo_first(self):
        product = self.make_product()
        GalleryProduct.objects.create(product=product, photos=image_file('g.jpg', fmt='JPEG'))
        post = InstagramPost.objects.create(product=product, caption='x')
        urls = services.prepare_images(post)
        self.assertEqual(len(urls), 2)
        for index, url in enumerate(urls, start=1):
            self.assertTrue(url.startswith('https://piedrasdelrayadito.cl/public/instagram/'))
            self.assertIn(f'/{post.pk}/{index}', url)

    @override_settings(BACKEND_BASE_URL='')
    def test_prepare_images_needs_a_public_backend_url(self):
        post = InstagramPost.objects.create(product=self.make_product(), caption='x')
        with self.assertRaisesMessage(instagram.InstagramError, 'BACKEND_BASE_URL'):
            services.prepare_images(post)


@CONNECTED
class InstagramClientTests(TestCase):
    def test_single_photo_flow(self):
        calls = []

        def fake_post(url, data, timeout):
            calls.append(('POST', url, data))
            if url.endswith('/media'):
                return FakeResponse({'id': 'container-1'})
            return FakeResponse({'id': 'media-1'})

        def fake_get(url, params, timeout):
            calls.append(('GET', url, params))
            if params['fields'] == 'permalink':
                return FakeResponse({'permalink': 'https://www.instagram.com/p/abc/'})
            return FakeResponse({'status_code': 'FINISHED'})

        with mock.patch('social.instagram.requests.post', side_effect=fake_post), \
                mock.patch('social.instagram.requests.get', side_effect=fake_get):
            result = instagram.publish_images(['https://x/1.jpg'], 'Hola', sleep=lambda s: None)

        self.assertEqual(result, ('media-1', 'https://www.instagram.com/p/abc/'))
        method, url, data = calls[0]
        self.assertEqual(url, 'https://graph.instagram.com/v23.0/17841400000000000/media')
        self.assertEqual(data['image_url'], 'https://x/1.jpg')
        self.assertEqual(data['caption'], 'Hola')
        publish = [c for c in calls if c[1].endswith('/media_publish')]
        self.assertEqual(publish[0][2]['creation_id'], 'container-1')

    def test_carousel_creates_children_then_parent(self):
        created = []

        def fake_post(url, data, timeout):
            if url.endswith('/media'):
                created.append(data)
                return FakeResponse({'id': f'c{len(created)}'})
            return FakeResponse({'id': 'media-9'})

        with mock.patch('social.instagram.requests.post', side_effect=fake_post), \
                mock.patch('social.instagram.requests.get',
                           return_value=FakeResponse({'status_code': 'FINISHED'})):
            instagram.publish_images(['https://x/1.jpg', 'https://x/2.jpg'], 'Hola',
                                     sleep=lambda s: None)

        self.assertEqual(created[0]['is_carousel_item'], 'true')
        self.assertNotIn('caption', created[0])
        self.assertEqual(created[2]['media_type'], 'CAROUSEL')
        self.assertEqual(created[2]['children'], 'c1,c2')
        self.assertEqual(created[2]['caption'], 'Hola')

    def test_container_error_stops_before_publishing(self):
        with mock.patch('social.instagram.requests.post',
                        return_value=FakeResponse({'id': 'c1'})) as post, \
                mock.patch('social.instagram.requests.get',
                           return_value=FakeResponse({'status_code': 'ERROR',
                                                      'status': 'bad image'})):
            with self.assertRaisesMessage(instagram.InstagramError, 'bad image'):
                instagram.publish_images(['https://x/1.jpg'], 'Hola', sleep=lambda s: None)
        self.assertFalse(any(c.args[0].endswith('/media_publish') for c in post.call_args_list))

    def test_errors_never_leak_the_token(self):
        def boom(*args, **kwargs):
            raise ConnectionError('failed url /media?access_token=secret-token')

        with mock.patch('social.instagram.requests.post', side_effect=boom):
            with self.assertRaises(instagram.InstagramError) as ctx:
                instagram.publish_images(['https://x/1.jpg'], 'Hola')
        self.assertNotIn('secret-token', str(ctx.exception))

    def test_meta_error_message_is_reported(self):
        payload = {'error': {'message': 'Invalid OAuth access token', 'code': 190}}
        with mock.patch('social.instagram.requests.post',
                        return_value=FakeResponse(payload, status_code=400)):
            with self.assertRaisesMessage(instagram.InstagramError, 'code 190'):
                instagram.publish_images(['https://x/1.jpg'], 'Hola')


@CONNECTED
class PublishPostTests(ProductMixin, TestCase):
    def setUp(self):
        self.product = self.make_product()
        self.post = InstagramPost.objects.create(product=self.product, caption='Hola')
        push = mock.patch('notifications.services.push_admins', return_value=0)
        self.push = push.start()
        self.addCleanup(push.stop)

    def test_success_marks_post_published(self):
        with mock.patch('social.instagram.publish_images',
                        return_value=('m1', 'https://www.instagram.com/p/abc/')) as publish:
            self.assertTrue(services.publish_post(self.post))
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, InstagramPost.Status.PUBLISHED)
        self.assertEqual(self.post.media_id, 'm1')
        self.assertEqual(self.post.attempts, 1)
        self.assertIsNotNone(self.post.published_at)
        self.assertEqual(publish.call_args.args[1], 'Hola')
        self.assertEqual(self.push.call_args.kwargs['title'], 'Publicado en Instagram')

    def test_failure_is_retried_then_marked_failed(self):
        error = instagram.InstagramError('token vencido')
        with mock.patch('social.instagram.publish_images', side_effect=error):
            for attempt in range(1, services.MAX_ATTEMPTS + 1):
                self.assertFalse(services.publish_post(self.post))
                self.post.refresh_from_db()
                self.assertEqual(self.post.attempts, attempt)
        self.assertEqual(self.post.status, InstagramPost.Status.FAILED)
        self.assertEqual(self.post.last_error, 'token vencido')
        self.assertEqual(self.push.call_count, 1)

    def test_post_taken_by_another_run_is_skipped(self):
        InstagramPost.objects.filter(pk=self.post.pk).update(
            status=InstagramPost.Status.PUBLISHING)
        with mock.patch('social.instagram.publish_images') as publish:
            self.assertFalse(services.publish_post(self.post))
        publish.assert_not_called()

    def test_stuck_post_is_failed_not_retried(self):
        InstagramPost.objects.filter(pk=self.post.pk).update(
            status=InstagramPost.Status.PUBLISHING,
            started_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(services.recover_stuck_posts(), 1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, InstagramPost.Status.FAILED)
        self.assertIn('puede que ya haya salido', self.post.last_error)


@CONNECTED
class PublishCommandTests(ProductMixin, TestCase):
    def run_command(self, *args):
        out, err = StringIO(), StringIO()
        call_command('publish_instagram', *args, stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def test_publishes_only_due_posts(self):
        product = self.make_product()
        due = InstagramPost.objects.create(product=product, caption='ya')
        later = InstagramPost.objects.create(
            product=product, caption='después',
            scheduled_for=timezone.now() + timedelta(hours=2))
        with mock.patch('social.management.commands.publish_instagram.publish_post', return_value=True) as publish:
            out, _ = self.run_command()
        self.assertEqual([c.args[0].pk for c in publish.call_args_list], [due.pk])
        self.assertIn('Published 1 post(s).', out)
        later.refresh_from_db()
        self.assertEqual(later.status, InstagramPost.Status.SCHEDULED)

    def test_dry_run_does_not_publish(self):
        InstagramPost.objects.create(product=self.make_product(), caption='ya')
        with mock.patch('social.management.commands.publish_instagram.publish_post') as publish:
            out, _ = self.run_command('--dry-run')
        publish.assert_not_called()
        self.assertIn('1 post(s) are due.', out)

    @override_settings(INSTAGRAM_ACCESS_TOKEN='')
    def test_without_credentials_posts_wait(self):
        post = InstagramPost.objects.create(product=self.make_product(), caption='ya')
        with mock.patch('social.management.commands.publish_instagram.publish_post') as publish:
            _, err = self.run_command()
        publish.assert_not_called()
        self.assertIn('left waiting', err)
        post.refresh_from_db()
        self.assertEqual(post.status, InstagramPost.Status.SCHEDULED)


@CONNECTED
class AdminInstagramApiTests(ProductMixin, APITestCase):
    url = '/api/admin/instagram/posts/'

    def setUp(self):
        self.staff = User.objects.create_user(
            email='duena@rayadito.cl', password='x', first_name='D', last_name='R',
            is_staff=True)
        self.client.force_authenticate(self.staff)
        self.product = self.make_product()

    def test_requires_staff(self):
        customer = User.objects.create_user(
            email='cliente@rayadito.cl', password='x', first_name='C', last_name='L')
        self.client.force_authenticate(customer)
        response = self.client.post(self.url, {'product': self.product.pk}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_schedule_now_uses_suggested_caption(self):
        response = self.client.post(self.url, {'product': self.product.pk}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        post = InstagramPost.objects.get()
        self.assertEqual(post.caption, services.build_caption(self.product))
        self.assertEqual(post.created_by, self.staff)
        self.assertLessEqual(post.scheduled_for, timezone.now())

    def test_schedule_later_with_custom_caption(self):
        when = timezone.now() + timedelta(days=1)
        response = self.client.post(self.url, {
            'product': self.product.pk, 'caption': '  Nueva pieza  ',
            'scheduled_for': when.isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        post = InstagramPost.objects.get()
        self.assertEqual(post.caption, 'Nueva pieza')
        self.assertEqual(post.scheduled_for, when)

    def test_rejects_past_date_draft_product_and_duplicates(self):
        past = (timezone.now() - timedelta(hours=1)).isoformat()
        response = self.client.post(self.url, {'product': self.product.pk,
                                               'scheduled_for': past}, format='json')
        self.assertEqual(response.status_code, 400)

        draft = self.make_product(name='Borrador', status=Product.ProductStatus.DRAFT)
        response = self.client.post(self.url, {'product': draft.pk}, format='json')
        self.assertEqual(response.status_code, 400)

        self.client.post(self.url, {'product': self.product.pk}, format='json')
        response = self.client.post(self.url, {'product': self.product.pk}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('ya tiene una publicación', str(response.data))

    def test_rejects_too_many_hashtags(self):
        caption = ' '.join(f'#tag{i}' for i in range(31))
        response = self.client.post(self.url, {'product': self.product.pk,
                                               'caption': caption}, format='json')
        self.assertEqual(response.status_code, 400)

    @override_settings(INSTAGRAM_USER_ID='')
    def test_not_connected_is_503(self):
        response = self.client.post(self.url, {'product': self.product.pk}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertFalse(InstagramPost.objects.exists())

    def test_cancel_only_scheduled(self):
        post = InstagramPost.objects.create(product=self.product, caption='x')
        self.assertEqual(self.client.delete(f'{self.url}{post.pk}/').status_code, 204)
        post.refresh_from_db()
        self.assertEqual(post.status, InstagramPost.Status.CANCELLED)
        self.assertEqual(self.client.delete(f'{self.url}{post.pk}/').status_code, 409)
        self.assertEqual(self.client.delete(f'{self.url}999999/').status_code, 404)

    def test_list_filters_by_product(self):
        other = self.make_product(name='Aros')
        InstagramPost.objects.create(product=self.product, caption='a')
        InstagramPost.objects.create(product=other, caption='b')
        response = self.client.get(self.url, {'product': self.product.pk})
        self.assertEqual([p['caption'] for p in response.data], ['a'])

    def test_draft_returns_suggestion(self):
        response = self.client.get(f'{self.url}draft/', {'product': self.product.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['configured'])
        self.assertTrue(response.data['publishable'])
        self.assertEqual(response.data['photo_count'], 1)
        self.assertEqual(response.data['caption'], services.build_caption(self.product))
        self.assertEqual(self.client.get(f'{self.url}draft/', {'product': 'x'}).status_code, 404)

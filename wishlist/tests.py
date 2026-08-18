from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from category.models import Category
from product.models import Product

from .models import WishlistItem

User = get_user_model()


class WishlistApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='wish@example.com', password='pass12345',
        )
        self.other = User.objects.create_user(
            email='other@example.com', password='pass12345',
        )
        self.category = Category.objects.create(name='Anillos')
        self.product = Product.objects.create(
            name='Anillo ágata', description='Pieza única', price=25000,
            category=self.category, photo='photos/x.jpg',
        )
        self.product2 = Product.objects.create(
            name='Collar jaspe', description='Otra pieza', price=30000,
            category=self.category, photo='photos/y.jpg',
        )

    def test_add_requires_auth(self):
        res = self.client.post('/api/wishlist/add', {'product_id': self.product.id})
        self.assertIn(res.status_code, (401, 403))

    def test_add_and_list(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/api/wishlist/add', {'product_id': self.product.id})
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data['created'])

        res = self.client.get('/api/wishlist/list')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['wishlist'][0]['product']['id'], self.product.id)

    def test_add_is_idempotent(self):
        self.client.force_authenticate(self.user)
        self.client.post('/api/wishlist/add', {'product_id': self.product.id})
        res = self.client.post('/api/wishlist/add', {'product_id': self.product.id})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data['created'])
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)

    def test_add_missing_product_id(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/api/wishlist/add', {})
        self.assertEqual(res.status_code, 400)

    def test_add_nonexistent_product(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/api/wishlist/add', {'product_id': 999999})
        self.assertEqual(res.status_code, 404)

    def test_remove(self):
        self.client.force_authenticate(self.user)
        self.client.post('/api/wishlist/add', {'product_id': self.product.id})
        res = self.client.delete(f'/api/wishlist/remove/{self.product.id}')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['removed'])
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 0)

    def test_remove_absent_is_noop(self):
        self.client.force_authenticate(self.user)
        res = self.client.delete(f'/api/wishlist/remove/{self.product.id}')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data['removed'])

    def test_user_only_sees_own_wishlist(self):
        WishlistItem.objects.create(user=self.other, product=self.product)
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/wishlist/list')
        self.assertEqual(res.data['count'], 0)

from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category


class CategoryApiTests(APITestCase):
    def test_empty_list_returns_200_not_500(self):
        # Sin categorías: lista vacía es un resultado válido, no un 500.
        res = self.client.get('/api/category/categories')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['categories'], [])

        res_p = self.client.get('/api/category/piedrascategory')
        self.assertEqual(res_p.status_code, status.HTTP_200_OK)
        self.assertEqual(res_p.data['categories'], [])

    def test_tree_with_subcategories(self):
        anillos = Category.objects.create(name='Anillos', ProductType='Joya')
        Category.objects.create(name='Anillos de plata', ProductType='Joya', parent=anillos)
        # Una categoría de otro tipo no debe aparecer en la de joyas.
        Category.objects.create(name='Ágatas', ProductType='Piedra')

        res = self.client.get('/api/category/categories')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['categories']), 1)
        root = res.data['categories'][0]
        self.assertEqual(root['name'], 'Anillos')
        self.assertEqual(len(root['sub_categories']), 1)
        self.assertEqual(root['sub_categories'][0]['name'], 'Anillos de plata')

    def test_get_category_ok(self):
        cat = Category.objects.create(name='Aros', ProductType='Joya')
        res = self.client.get(f'/api/category/get-category/{cat.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['category']['name'], 'Aros')

    def test_get_missing_category_returns_404(self):
        res = self.client.get('/api/category/get-category/9999')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_category_bad_id_returns_400(self):
        res = self.client.get('/api/category/get-category/abc')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

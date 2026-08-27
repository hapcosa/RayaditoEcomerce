"""Rutas de la API admin de productos. Montadas en /api/admin/ (ver core/urls.py)."""
from rest_framework.routers import DefaultRouter

from .admin_api import AdminCategoryViewSet, AdminProductViewSet

app_name = 'admin_product'

router = DefaultRouter()
router.register('products', AdminProductViewSet, basename='admin-product')
router.register('categories', AdminCategoryViewSet, basename='admin-category')

urlpatterns = router.urls

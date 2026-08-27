"""Rutas de la API admin de pedidos. Montadas en /api/admin/ (ver core/urls.py)."""
from rest_framework.routers import DefaultRouter

from .admin_api import AdminOrderViewSet

app_name = 'admin_orders'

router = DefaultRouter()
router.register('orders', AdminOrderViewSet, basename='admin-order')

urlpatterns = router.urls

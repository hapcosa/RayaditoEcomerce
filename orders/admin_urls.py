"""Rutas de la API admin de pedidos. Montadas en /api/admin/ (ver core/urls.py)."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .admin_api import AdminOrderViewSet
from .admin_stats import AdminStatsView
from .admin_withdrawals import AdminWithdrawalViewSet

app_name = 'admin_orders'

router = DefaultRouter()
router.register('orders', AdminOrderViewSet, basename='admin-order')
router.register('withdrawals', AdminWithdrawalViewSet, basename='admin-withdrawal')

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
] + router.urls

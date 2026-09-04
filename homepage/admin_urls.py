"""Rutas de la API admin de portada. Montadas en /api/admin/ (ver core/urls.py)."""
from rest_framework.routers import DefaultRouter

from .admin_api import AdminHeroImageViewSet

app_name = 'admin_homepage'

router = DefaultRouter()
router.register('hero-images', AdminHeroImageViewSet, basename='admin-hero-image')

urlpatterns = router.urls

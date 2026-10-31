"""Rutas de la API admin de portada. Montadas en /api/admin/ (ver core/urls.py)."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .admin_api import AdminHeroImageViewSet, AdminHomepageSettingsView

app_name = 'admin_homepage'

router = DefaultRouter()
router.register('hero-images', AdminHeroImageViewSet, basename='admin-hero-image')

urlpatterns = [
    path('homepage-settings/', AdminHomepageSettingsView.as_view(),
         name='admin-homepage-settings'),
] + router.urls

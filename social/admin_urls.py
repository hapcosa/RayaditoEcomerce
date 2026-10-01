"""Rutas de redes sociales para staff. Montadas en /api/admin/ (ver core/urls.py)."""
from rest_framework.routers import DefaultRouter

from .admin_api import InstagramPostViewSet

app_name = 'admin_social'

router = DefaultRouter()
router.register('instagram/posts', InstagramPostViewSet, basename='admin-instagram-post')

urlpatterns = router.urls

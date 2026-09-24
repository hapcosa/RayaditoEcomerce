"""Rutas de avisos para staff. Montadas en /api/admin/ (ver core/urls.py)."""
from django.urls import path

from .admin_api import AdminPushTokenView

app_name = 'admin_notifications'

urlpatterns = [
    path('push-tokens/', AdminPushTokenView.as_view()),
]

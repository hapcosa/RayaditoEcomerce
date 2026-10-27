"""Vistas propias del proyecto (no de una app concreta)."""
from django.conf import settings
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


def page_not_found(request, exception=None):
    """404 del backend en JSON.

    Django ya no sirve la tienda: el SPA de Vite y su catch-all se retiraron al
    migrar a Next.js. Si una peticion llega hasta aca sin coincidir con ninguna
    ruta, es una URL de backend equivocada (o el proxy mando mal el trafico),
    y devolver HTML solo confundiria al cliente de la API.
    """
    return JsonResponse(
        {'error': 'No existe esta ruta en el backend.', 'path': request.path},
        status=404,
    )


class StoreConfigView(APIView):
    """`GET /api/store/`: identidad de la tienda y sus catálogos (store.json).

    Público: es la misma información que muestra la tienda. La app admin lo usa
    para saber qué catálogos ofrecer al cargar un producto.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        return Response(settings.STORE)

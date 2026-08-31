"""Vistas propias del proyecto (no de una app concreta)."""
from django.http import JsonResponse


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

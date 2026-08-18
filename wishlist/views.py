"""API de la lista de deseos. Rutas montadas en /api/wishlist/.

Todas requieren autenticación (JWT). Cada usuario solo ve y modifica la suya.
"""
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from product.models import Product

from .models import WishlistItem
from .serializers import WishlistItemSerializer


class ListWishlistView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related('product')
        return Response(
            {
                'wishlist': WishlistItemSerializer(items, many=True).data,
                'count': items.count(),
            },
            status=status.HTTP_200_OK,
        )


class AddWishlistView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        product_id = request.data.get('product_id')
        if product_id is None:
            return Response(
                {'detail': 'product_id es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        product = get_object_or_404(Product, id=product_id)
        item, created = WishlistItem.objects.get_or_create(
            user=request.user, product=product,
        )
        return Response(
            {
                'item': WishlistItemSerializer(item).data,
                'created': created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RemoveWishlistView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, product_id):
        deleted, _ = WishlistItem.objects.filter(
            user=request.user, product_id=product_id,
        ).delete()
        return Response(
            {'removed': bool(deleted)},
            status=status.HTTP_200_OK,
        )

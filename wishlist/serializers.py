from rest_framework import serializers

from product.serializers import ProductSerializer

from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    """Salida: el ítem con el producto completo embebido (para pintar la ficha)."""

    product = ProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'created_at')
        read_only_fields = fields

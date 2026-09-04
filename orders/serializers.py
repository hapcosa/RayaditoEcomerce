"""Serializers de pedidos para el cliente autenticado (`/api/orders/`).

Contraparte "cliente" de `orders/admin_api.py`: el dueño ve todos los pedidos
por `/api/admin/orders/`, el cliente solo los suyos por estos endpoints.

Dinero siempre en entero CLP (`PositiveIntegerField`), nunca floats.
"""
from rest_framework import serializers

from shipping.serializers import ShippingSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Ítem de un pedido, con lo mínimo para enlazar al producto en el sitio.

    `product_*` viene de la FK y puede ser null si el producto fue borrado.
    Los datos de nombre/precio están congelados en el OrderItem a propósito:
    reflejan lo que el cliente compró, no lo que el catálogo dice hoy.
    """
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_photo = serializers.ImageField(source='product.photo', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'name', 'price', 'count',
            'product_id', 'product_slug', 'product_photo',
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Fila del listado "Mis pedidos". Sin ítems, para no inflar la respuesta."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    shipping = ShippingSerializer(source='shipping_id', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display', 'transaction_id',
            'amount', 'shipping_price', 'date_issued',
            'address_line_1', 'city', 'deliveryNumber',
            'items_count', 'shipping',
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detalle de un pedido propio, con ítems y número de seguimiento."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    shipping = ShippingSerializer(source='shipping_id', read_only=True)
    order_items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display', 'transaction_id',
            'amount', 'shipping_price', 'date_issued',
            'full_name', 'email', 'address_line_1', 'city',
            'postal_zip_code', 'region', 'region_display', 'telephone_number',
            'deliveryNumber', 'shipping', 'order_items',
        ]

    def get_email(self, obj):
        """El pedido guarda `email` solo en compras invitado; si no, el del usuario."""
        return obj.email or (obj.user.email if obj.user else None)

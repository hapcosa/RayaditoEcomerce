"""API de pedidos para staff (app admin Expo). Montada en /api/admin/.

Todo requiere `IsAdminUser`. Incluye listado/detalle de todos los pedidos y un
endpoint de cambio de estado con **máquina de estados** (transiciones válidas).

Nota de scope: el descuento/reposición de stock es responsabilidad de Fase 2
(pagos); aquí solo se cambia el estado operativo del pedido.
"""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Order, OrderItem

# Transiciones válidas de la máquina de estados de un pedido.
# Estados (Order.OrderStatus): no procesado, procesado, enviado, cancelado, rechazado.
S = Order.OrderStatus
ORDER_TRANSITIONS = {
    S.not_processed: {S.processed, S.cancelled, S.refused},
    S.processed: {S.shipping, S.cancelled, S.refused},
    S.shipping: set(),      # terminal (entregado/en tránsito)
    S.cancelled: set(),     # terminal
    S.refused: set(),       # terminal
}


class AdminOrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'name', 'price', 'count', 'date_added']


class AdminOrderSerializer(serializers.ModelSerializer):
    items = AdminOrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    allowed_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'transaction_id', 'amount', 'shipping_price',
            'full_name', 'email', 'address_line_1', 'city', 'postal_zip_code',
            'region', 'telephone_number', 'deliveryNumber', 'date_issued',
            'items', 'allowed_transitions',
        ]

    def get_allowed_transitions(self, obj):
        return sorted(str(s) for s in ORDER_TRANSITIONS.get(obj.status, set()))


class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Listado/detalle de todos los pedidos + cambio de estado (staff)."""
    serializer_class = AdminOrderSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        qs = (
            Order.objects.select_related('shipping_id')
            .prefetch_related('orderitem_set')
            .order_by('-date_issued')
        )
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        order = self.get_object()
        new_status = str(request.data.get('status') or '').strip()

        valid_values = {str(choice) for choice in S.values}
        if new_status not in valid_values:
            return Response(
                {'error': f'Estado inválido. Opciones: {sorted(valid_values)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_status == order.status:
            return Response(
                {'error': 'El pedido ya está en ese estado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_status not in ORDER_TRANSITIONS.get(order.status, set()):
            return Response(
                {
                    'error': f'Transición no permitida: {order.status} → {new_status}.',
                    'allowed_transitions': sorted(
                        str(s) for s in ORDER_TRANSITIONS.get(order.status, set())
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_fields = ['status']
        # Al despachar exigimos número de seguimiento (reusa lógica de DispatchOrderView).
        if new_status == S.shipping:
            delivery_number = str(
                request.data.get('deliveryNumber')
                or request.data.get('delivery_number')
                or ''
            ).strip()
            if not delivery_number:
                return Response(
                    {'error': 'deliveryNumber requerido para pasar a enviado.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.deliveryNumber = delivery_number
            update_fields.append('deliveryNumber')

        order.status = new_status
        order.save(update_fields=update_fields)
        return Response(AdminOrderSerializer(order).data, status=status.HTTP_200_OK)

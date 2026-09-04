"""Endpoints de pedidos para el cliente autenticado.

`DispatchOrderView` es staff y queda por compatibilidad; el camino nuevo para el
dueño es `orders/admin_api.py` (`PATCH /api/admin/orders/<id>/status/`).

Reglas: un usuario solo ve sus propios pedidos, en cualquier estado.
"""
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderDetailSerializer, OrderListSerializer


class DispatchOrderView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, order_id, format=None):
        delivery_number = str(
            request.data.get('deliveryNumber')
            or request.data.get('delivery_number')
            or ''
        ).strip()
        if not delivery_number:
            return Response(
                {'error': 'deliveryNumber requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(Order, id=order_id)
        order.deliveryNumber = delivery_number
        order.status = Order.OrderStatus.shipping
        order.save(update_fields=['deliveryNumber', 'status'])

        return Response(
            {
                'order': {
                    'id': order.id,
                    'status': order.status,
                    'deliveryNumber': order.deliveryNumber,
                }
            },
            status=status.HTTP_200_OK,
        )


class OwnOrdersMixin:
    """Restringe el queryset a los pedidos del usuario autenticado."""
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .select_related('shipping_id', 'user')
            .order_by('-date_issued')
        )


class ListOrdersView(OwnOrdersMixin, ListAPIView):
    """GET /api/orders/get-orders — pedidos del usuario, en cualquier estado."""
    serializer_class = OrderListSerializer
    pagination_class = None

    def get_queryset(self):
        return super().get_queryset().annotate(items_count=Count('orderitem'))

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({'orders': serializer.data}, status=status.HTTP_200_OK)


class ListOrderDetailView(OwnOrdersMixin, RetrieveAPIView):
    """GET /api/orders/get-order/<transactionId> — detalle de un pedido propio.

    El parámetro acepta el `transaction_id` de MercadoPago o, como fallback, el
    `id` numérico del pedido (así lo usa el front legacy).
    """
    serializer_class = OrderDetailSerializer

    def get_object(self):
        lookup = self.kwargs['transactionId']
        qs = self.get_queryset().prefetch_related('orderitem_set__product')

        order = qs.filter(transaction_id=lookup).first()
        if order is None and str(lookup).isdigit():
            order = qs.filter(id=int(lookup)).first()
        if order is None:
            raise Http404('No existe un pedido con ese identificador.')
        return order

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response({'order': serializer.data}, status=status.HTTP_200_OK)

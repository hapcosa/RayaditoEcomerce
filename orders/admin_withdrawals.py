"""Solicitudes de retracto para staff (app admin Expo). Montada en /api/admin/.

La tienda no sabe cuando llego el paquete, asi que el plazo legal (10 dias
desde la recepcion, 90 sin confirmacion escrita) lo evalua la duena: la API le
da las fechas del pedido para decidir, y registra la decision.

El reembolso en si se hace en MercadoPago; aca solo queda constancia de que se
hizo.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import WithdrawalRequest

W = WithdrawalRequest.Status
TRANSITIONS = {
    W.RECEIVED: {W.ACCEPTED, W.REJECTED},
    W.ACCEPTED: {W.REFUNDED},
    W.REFUNDED: set(),
    W.REJECTED: set(),
}
FINAL = {W.REFUNDED, W.REJECTED}
OPEN = (W.RECEIVED, W.ACCEPTED)


class WithdrawalOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    transaction_id = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    full_name = serializers.CharField(allow_null=True)
    telephone_number = serializers.CharField()
    amount = serializers.IntegerField(allow_null=True)
    shipping_price = serializers.IntegerField()
    paid_at = serializers.DateTimeField(allow_null=True)
    shipped_at = serializers.DateTimeField(allow_null=True)
    deliveryNumber = serializers.CharField(allow_null=True)


class AdminWithdrawalSerializer(serializers.ModelSerializer):
    order = WithdrawalOrderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    allowed_transitions = serializers.SerializerMethodField()

    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'code', 'status', 'status_display', 'email', 'reason',
            'staff_note', 'created_at', 'resolved_at', 'order', 'allowed_transitions',
        ]

    def get_allowed_transitions(self, obj):
        return sorted(str(s) for s in TRANSITIONS.get(obj.status, set()))


class AdminWithdrawalViewSet(viewsets.ReadOnlyModelViewSet):
    """Listado/detalle de solicitudes de retracto + cambio de estado."""
    serializer_class = AdminWithdrawalSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        qs = WithdrawalRequest.objects.select_related('order').order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter == 'open':
            qs = qs.filter(status__in=OPEN)
        elif status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        with transaction.atomic():
            withdrawal = (
                WithdrawalRequest.objects.select_for_update()
                .select_related('order').get(pk=self.get_object().pk)
            )
            new_status = str(request.data.get('status') or '').strip()
            note = str(request.data.get('staff_note') or '').strip()
            allowed = TRANSITIONS.get(withdrawal.status, set())

            if new_status not in {str(s) for s in W.values}:
                return Response(
                    {'error': f'Estado inválido. Opciones: {sorted(W.values)}'},
                    status=status.HTTP_400_BAD_REQUEST)
            if new_status not in allowed:
                return Response(
                    {'error': f'Transición no permitida: {withdrawal.status} → {new_status}.',
                     'allowed_transitions': sorted(str(s) for s in allowed)},
                    status=status.HTTP_400_BAD_REQUEST)
            # Un rechazo sin motivo deja a la tienda sin respaldo si el cliente
            # reclama en el SERNAC.
            if new_status == W.REJECTED and not (note or withdrawal.staff_note):
                return Response(
                    {'error': 'Para rechazar indica el motivo en la nota.'},
                    status=status.HTTP_400_BAD_REQUEST)

            withdrawal.status = new_status
            if note:
                withdrawal.staff_note = note
            if new_status in FINAL:
                withdrawal.resolved_at = timezone.now()
            withdrawal.save(update_fields=['status', 'staff_note', 'resolved_at'])
        return Response(AdminWithdrawalSerializer(withdrawal).data, status=status.HTTP_200_OK)

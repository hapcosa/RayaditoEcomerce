"""Formulario publico de retracto. Montado en /api/orders/withdrawal.

Publico a proposito: el derecho a retracto no puede depender de tener cuenta,
y muchos pedidos son de compra como invitado.
"""
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .withdrawal import create_withdrawal, find_order


class WithdrawalInputSerializer(serializers.Serializer):
    order_number = serializers.CharField(max_length=64)
    email = serializers.EmailField()
    reason = serializers.CharField(max_length=2000, required=False, allow_blank=True,
                                   default='')


class CreateWithdrawalView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    # Sin freno, el par numero+correo se podria probar por fuerza bruta.
    throttle_scope = 'withdrawal'

    def post(self, request):
        serializer = WithdrawalInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order = find_order(data['order_number'], data['email'])
        if order is None:
            return Response(
                {'message': 'No encontramos un pedido pagado con ese número y '
                            'ese correo. Revisa el correo de confirmación de tu '
                            'compra.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        withdrawal, created = create_withdrawal(order, data['email'], data['reason'])
        return Response(
            {
                'code': withdrawal.code,
                'created_at': withdrawal.created_at,
                'already_requested': not created,
                'message': (
                    'Recibimos tu solicitud de retracto.' if created
                    else 'Ya habías enviado una solicitud para este pedido.'
                ),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

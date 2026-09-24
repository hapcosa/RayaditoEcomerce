"""Registro de aparatos para push. Montado en /api/admin/ (ver core/urls.py).

Solo staff: los avisos que se mandan por este canal son de operacion interna
(ventas, plazos), nunca del cliente.
"""
from rest_framework import serializers, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DevicePushToken


class DevicePushTokenSerializer(serializers.ModelSerializer):
    # Sin el validador de unicidad que DRF agrega solo: registrar de nuevo un
    # aparato ya conocido es lo normal (la app revalida el token al abrir), y
    # ese validador lo convertiria en un 400.
    token = serializers.CharField(max_length=255)

    class Meta:
        model = DevicePushToken
        fields = ['token', 'platform', 'is_active', 'updated_at']
        read_only_fields = ['is_active', 'updated_at']


class AdminPushTokenView(APIView):
    """POST registra o revalida el aparato; DELETE lo da de baja."""
    permission_classes = (IsAdminUser,)

    def post(self, request, format=None):
        serializer = DevicePushTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token'].strip()
        if not token:
            return Response({'error': 'token requerido'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Upsert por token: Expo puede devolverle el mismo token a otro usuario
        # del mismo aparato, y reinstalar la app genera uno nuevo. Revalidar
        # tambien reactiva un token que se habia apagado.
        device, created = DevicePushToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'platform': serializer.validated_data.get(
                    'platform', DevicePushToken.Platform.UNKNOWN),
                'is_active': True,
                'last_error': '',
            },
        )
        return Response(
            DevicePushTokenSerializer(device).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, format=None):
        token = str(request.data.get('token') or '').strip()
        if not token:
            return Response({'error': 'token requerido'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Se desactiva en vez de borrarse: asi queda el rastro de que ese
        # aparato estuvo registrado y por que dejo de estarlo.
        DevicePushToken.objects.filter(token=token, user=request.user).update(
            is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

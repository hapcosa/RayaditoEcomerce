from django.db import transaction
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import UserProfile
from .serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    """Libreta de direcciones del usuario autenticado.

    El queryset se filtra siempre por `request.user`: la dirección de otra
    persona no se lista, ni se lee, ni se edita por id.
    """

    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        # La primera dirección queda por defecto sin que el usuario lo pida:
        # si no, el checkout no tendría ninguna preseleccionada.
        primera = not self.get_queryset().exists()
        pedida = serializer.validated_data.get('is_default', False)
        direccion = serializer.save(
            user=self.request.user,
            is_default=primera or pedida,
        )
        self._dejar_una_sola_por_defecto(direccion)

    @transaction.atomic
    def perform_update(self, serializer):
        direccion = serializer.save()
        if direccion.is_default:
            self._dejar_una_sola_por_defecto(direccion)
        elif not self.get_queryset().filter(is_default=True).exists():
            # Quitarle el default a la única marcada dejaría la libreta sin
            # preselección; se devuelve a esta misma.
            direccion.is_default = True
            direccion.save(update_fields=['is_default'])

    @transaction.atomic
    def perform_destroy(self, instance):
        era_default = instance.is_default
        instance.delete()
        if era_default:
            siguiente = self.get_queryset().first()
            if siguiente:
                siguiente.is_default = True
                siguiente.save(update_fields=['is_default'])

    def _dejar_una_sola_por_defecto(self, direccion):
        (self.get_queryset()
             .filter(is_default=True)
             .exclude(pk=direccion.pk)
             .update(is_default=False))

"""API de portada para staff (app admin Expo). Montada en /api/admin/.

Todo requiere `IsAdminUser`. Es el "panel" que pidio el dueño para cambiar la
foto de portada desde el celular: subir fotos (hasta `HeroImage.MAX_ACTIVAS`
activas; el resto queda archivado), reordenarlas y borrarlas.
"""
from rest_framework import serializers, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser

from .models import HeroImage


class OpcionalEnMultipartField(serializers.BooleanField):
    """`BooleanField` que, si no viene en el formulario, queda ausente.

    DRF trata un booleano ausente en multipart como `False` (regla de los
    checkboxes HTML, que no se envian cuando estan desmarcados). La app sube las
    fotos con multipart y no manda el campo, asi que cada foto nueva nacia
    desactivada y la portada no cambiaba nunca. Ausente, `validate()` decide.
    """
    default_empty_html = serializers.empty


class AdminHeroImageSerializer(serializers.ModelSerializer):
    is_active = OpcionalEnMultipartField(required=False)

    class Meta:
        model = HeroImage
        fields = [
            'id', 'image', 'alt_text', 'caption',
            'position', 'is_active', 'date_created',
        ]
        read_only_fields = ['date_created']

    def validate(self, attrs):
        """Traduce el limite del modelo a un 400 con mensaje, no a un 500.

        `HeroImage.clean()` es la regla real (aplica tambien desde el admin de
        Django y desde un shell), pero DRF no la corre sola: hay que armar la
        instancia resultante y llamarla explicitamente.

        Una foto nueva que no dice si va activa entra a la portada si hay cupo
        y, si esta llena, queda archivada: subir no tiene que depender de
        sacar antes otra foto.
        """
        if self.instance is None and 'is_active' not in attrs:
            activas = HeroImage.objects.filter(is_active=True).count()
            attrs['is_active'] = activas < HeroImage.MAX_ACTIVAS
        candidata = HeroImage(
            pk=self.instance.pk if self.instance else None,
            is_active=attrs.get(
                'is_active',
                self.instance.is_active if self.instance else True,
            ),
        )
        candidata.clean()
        return attrs


class AdminHeroImageViewSet(viewsets.ModelViewSet):
    """CRUD de fotos de portada.

    Lista todas (activas e inactivas) para que la app pueda mostrar el archivo
    completo y dejar rotar la portada sin volver a subir fotos.
    """
    queryset = HeroImage.objects.all()
    serializer_class = AdminHeroImageSerializer
    permission_classes = (IsAdminUser,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = None

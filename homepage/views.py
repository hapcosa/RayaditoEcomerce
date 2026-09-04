"""API publica de la portada. Montada en /api/homepage/."""
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import HeroImage
from .serializers import HeroImageSerializer


class HeroImageListView(ListAPIView):
    """Fotos activas de la portada, en el orden en que el dueño las puso.

    Sin paginar: son tres como maximo (`HeroImage.MAX_ACTIVAS`) y el front las
    consume como una lista completa para armar el mosaico escalonado.
    """
    serializer_class = HeroImageSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        return HeroImage.objects.filter(is_active=True)[:HeroImage.MAX_ACTIVAS]

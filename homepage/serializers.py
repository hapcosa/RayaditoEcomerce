from rest_framework import serializers

from .models import HeroImage


class HeroImageSerializer(serializers.ModelSerializer):
    """Foto de portada para el sitio publico. Solo lectura."""

    # Tamaño real del archivo. El mosaico dibuja cada foto con SU proporción en
    # vez de recortarla contra una fija, y `next/image` necesita las medidas
    # para reservar el hueco antes de que cargue (si no, la portada salta).
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()

    class Meta:
        model = HeroImage
        fields = ['id', 'image', 'alt_text', 'caption', 'position', 'width', 'height']

    def _medidas(self, obj):
        """`(ancho, alto)` o `(None, None)` si el archivo no se puede leer.

        Abrir la imagen toca el disco: si el archivo se borró a mano, Pillow
        levanta y sin esto se caía toda la portada por una foto rota.
        """
        try:
            return obj.image.width, obj.image.height
        except Exception:
            return None, None

    def get_width(self, obj):
        return self._medidas(obj)[0]

    def get_height(self, obj):
        return self._medidas(obj)[1]

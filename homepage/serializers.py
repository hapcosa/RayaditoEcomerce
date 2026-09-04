from rest_framework import serializers

from .models import HeroImage


class HeroImageSerializer(serializers.ModelSerializer):
    """Foto de portada para el sitio publico. Solo lectura."""

    class Meta:
        model = HeroImage
        fields = ['id', 'image', 'alt_text', 'caption', 'position']

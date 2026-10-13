"""Publicaciones de Instagram desde la app admin. Montado en /api/admin/.

La app solo programa: el comando `publish_instagram` es el que publica (ver
services.py). Programar "para ya" deja la publicacion lista para la proxima
corrida del timer, a lo mas unos minutos despues.
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from product.models import Product

from . import instagram
from .models import InstagramPost
from .services import (
    CAPTION_MAX_CHARS, HASHTAG_MAX, build_caption, product_photos, product_url,
)

ACTIVE_STATUSES = (InstagramPost.Status.SCHEDULED, InstagramPost.Status.PUBLISHING)
# Margen para el reloj del telefono: una hora "de ahora" que llega un par de
# minutos atrasada no es un error de la duena.
PAST_TOLERANCE = timedelta(minutes=5)


class InstagramPostSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    caption = serializers.CharField(required=False, allow_blank=True,
                                    max_length=CAPTION_MAX_CHARS)
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = InstagramPost
        fields = [
            'id', 'product', 'product_name', 'caption', 'status', 'scheduled_for',
            'attempts', 'permalink', 'last_error', 'created_at', 'published_at',
        ]
        read_only_fields = [
            'id', 'status', 'attempts', 'permalink', 'last_error', 'created_at',
            'published_at',
        ]

    def validate_product(self, product):
        if product.status != Product.ProductStatus.PUBLISHED:
            raise serializers.ValidationError(
                'Solo se pueden publicar productos visibles en la tienda.')
        if not product_photos(product):
            raise serializers.ValidationError('El producto no tiene fotos.')
        if product.instagram_posts.filter(status__in=ACTIVE_STATUSES).exists():
            raise serializers.ValidationError(
                'Este producto ya tiene una publicación programada.')
        return product

    def validate_caption(self, caption):
        if caption.count('#') > HASHTAG_MAX:
            raise serializers.ValidationError(
                f'Instagram acepta hasta {HASHTAG_MAX} hashtags.')
        return caption.strip()

    def validate_scheduled_for(self, value):
        now = timezone.now()
        if value is None:
            return now
        if value < now - PAST_TOLERANCE:
            raise serializers.ValidationError('La fecha ya pasó.')
        return max(value, now)

    def create(self, validated_data):
        validated_data.setdefault('scheduled_for', timezone.now())
        if not validated_data.get('caption'):
            validated_data['caption'] = build_caption(validated_data['product'])
        return super().create(validated_data)


class InstagramPostViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                           mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """GET lista (filtrable por ?product=), POST programa, DELETE cancela."""
    serializer_class = InstagramPostSerializer
    permission_classes = (IsAdminUser,)
    pagination_class = None

    def get_queryset(self):
        queryset = InstagramPost.objects.select_related('product')
        product = self.request.query_params.get('product')
        if product:
            if not product.isdigit():
                return queryset.none()
            queryset = queryset.filter(product_id=product)
        return queryset

    def create(self, request, *args, **kwargs):
        if not instagram.is_configured():
            return Response(
                {'error': 'Instagram no está conectado todavía '
                          '(falta INSTAGRAM_USER_ID o el token: manage.py instagram_token set).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # Cancelar en vez de borrar: queda el rastro, y una publicada no se
        # puede deshacer desde aca (habria que borrarla en Instagram).
        updated = InstagramPost.objects.filter(
            pk=kwargs['pk'], status=InstagramPost.Status.SCHEDULED,
        ).update(status=InstagramPost.Status.CANCELLED)
        if not updated:
            if not InstagramPost.objects.filter(pk=kwargs['pk']).exists():
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(
                {'error': 'Solo se puede cancelar una publicación programada.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='draft')
    def draft(self, request):
        """Borrador para la app: texto sugerido y si Instagram esta conectado."""
        product_id = request.query_params.get('product', '')
        product = (
            Product.objects.filter(pk=product_id).first()
            if product_id.isdigit() else None
        )
        if product is None:
            return Response({'error': 'Producto no encontrado.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({
            'configured': instagram.is_configured(),
            'caption': build_caption(product),
            'photo_count': len(product_photos(product)),
            'product_url': product_url(product),
            'publishable': product.status == Product.ProductStatus.PUBLISHED,
        })

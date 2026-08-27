"""API de escritura para staff (app admin Expo). Montada en /api/admin/.

Todo requiere `IsAdminUser` (== `is_staff`). El modelo de producto se maneja a
nivel de `Product` base (no las subclases Joyas/Piedras); las variantes quedan
fuera de scope. Dinero en entero CLP (ver AGENTS.md).
"""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from category.models import Category

from .models import GalleryProduct, Product


class AdminCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'ProductType']


class AdminCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Listado plano de categorías para el picker de la app admin.

    Read-only a propósito: crear/editar categorías no es parte del DoD de la
    Fase 5. Devuelve todas las categorías (sin filtrar por Joya/Piedra) para que
    el formulario de alta de producto pueda elegir cualquiera.
    """
    queryset = Category.objects.order_by('ProductType', 'name')
    serializer_class = AdminCategorySerializer
    permission_classes = (IsAdminUser,)
    pagination_class = None


class AdminGalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryProduct
        fields = ['id', 'product', 'photos']
        read_only_fields = ['product']


class AdminProductSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    available_stock = serializers.IntegerField(read_only=True)
    gallery = AdminGalleryImageSerializer(
        source='galleryproduct_set', many=True, read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'product_type', 'photo', 'description',
            'price', 'compare_price', 'category', 'status', 'is_featured',
            'sold', 'available_stock', 'date_created', 'gallery',
        ]
        read_only_fields = ['id', 'slug', 'available_stock', 'date_created']

    def validate_price(self, value):
        # Dinero en entero CLP, sin decimales ni negativos.
        if value < 0:
            raise serializers.ValidationError('El precio debe ser un entero CLP >= 0.')
        return value

    def validate_compare_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'compare_price debe ser un entero CLP >= 0.')
        return value


class AdminProductViewSet(viewsets.ModelViewSet):
    """CRUD de productos para staff + subida de imágenes a la galería."""
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related('galleryproduct_set')
        .order_by('-date_created')
    )
    serializer_class = AdminProductSerializer
    permission_classes = (IsAdminUser,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @action(detail=True, methods=['post'], url_path='images')
    def add_images(self, request, pk=None):
        """Sube una o varias imágenes (multipart, campo `images`) a la galería."""
        product = self.get_object()
        files = request.FILES.getlist('images') or request.FILES.getlist('photos')
        if not files:
            return Response(
                {'error': 'Adjunta al menos una imagen en el campo `images`.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        created = [
            GalleryProduct.objects.create(product=product, photos=f) for f in files
        ]
        return Response(
            {'gallery': AdminGalleryImageSerializer(created, many=True).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['delete'], url_path=r'images/(?P<image_id>\d+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Borra una imagen de la galería del producto."""
        product = self.get_object()
        deleted, _ = GalleryProduct.objects.filter(
            product=product, id=image_id).delete()
        if not deleted:
            return Response(
                {'error': 'Imagen no encontrada en este producto.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

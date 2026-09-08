"""API de escritura para staff (app admin Expo). Montada en /api/admin/.

Todo requiere `IsAdminUser` (== `is_staff`). El modelo de producto se maneja a
nivel de `Product` base (no las subclases Joyas/Piedras); las variantes quedan
fuera de scope. Dinero en entero CLP (ver AGENTS.md).

Como esta API no crea las subclases, `product_type` es lo unico que decide en
que catalogo publico aparece el producto: por eso aca es obligatorio y solo
acepta 'joya' o 'piedra'. Sin el, el producto queda 'general' e invisible en la
tienda.
"""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from category.models import Category

from .models import GalleryProduct, Product


class AdminCategorySerializer(serializers.ModelSerializer):
    # Cuántos productos cuelgan de la categoría: la app lo muestra y lo usa para
    # avisar antes de intentar borrar.
    product_count = serializers.IntegerField(source='product_set.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'ProductType', 'product_count']

    def validate_ProductType(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Indicá el rubro (ej. Joya o Piedra).')
        return value

    def validate_parent(self, value):
        # Un ciclo dejaría el árbol de categorías irrecorrible (ver category/views).
        if value is None:
            return value
        node = value
        seen = set()
        while node is not None:
            if self.instance is not None and node.pk == self.instance.pk:
                raise serializers.ValidationError(
                    'Una categoría no puede colgar de sí misma ni de una hija suya.'
                )
            if node.pk in seen:
                break
            seen.add(node.pk)
            node = node.parent
        return value


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """CRUD de categorías para la app admin.

    Devuelve todas las categorías (sin filtrar por Joya/Piedra) para que el
    formulario de alta de producto pueda elegir cualquiera. `ProductType` es
    texto libre a propósito: el repo es template multi-rubro (ver AGENTS.md), un
    fork textil crea "Polera" sin tocar el modelo.
    """
    queryset = Category.objects.order_by('ProductType', 'name')
    serializer_class = AdminCategorySerializer
    permission_classes = (IsAdminUser,)
    pagination_class = None

    def destroy(self, request, *args, **kwargs):
        """Borra solo si la categoría está vacía.

        `Product.category` y `Category.parent` son CASCADE: borrar de un tap
        desde el teléfono se llevaría productos y subcategorías por delante.
        """
        category = self.get_object()
        products = category.product_set.count()
        children = category.children.count()
        if products or children:
            return Response(
                {'detail': (
                    f'No se puede borrar: tiene {products} producto(s) y '
                    f'{children} subcategoría(s). Movelos o borralos primero.'
                )},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)


class AdminGalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryProduct
        fields = ['id', 'product', 'photos']
        read_only_fields = ['product']


class AdminProductSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    # Obligatorio y sin 'general': un producto creado desde la app tiene que
    # caer en un catalogo publico.
    product_type = serializers.ChoiceField(
        choices=[
            (Product.ProductType.JOYA, Product.ProductType.JOYA.label),
            (Product.ProductType.PIEDRA, Product.ProductType.PIEDRA.label),
        ],
    )
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

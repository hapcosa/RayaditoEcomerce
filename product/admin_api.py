"""API de escritura para staff (app admin Expo). Montada en /api/admin/.

Todo requiere `IsAdminUser` (== `is_staff`). El modelo de producto se maneja a
nivel de `Product` base (no las subclases Joyas/Piedras); las variantes quedan
fuera de scope. Dinero en entero CLP (ver AGENTS.md).

Como esta API no crea las subclases, `product_type` es lo unico que decide en
que catalogo publico aparece el producto: por eso aca es obligatorio y solo
acepta 'joya' o 'piedra'. Sin el, el producto queda 'general' e invisible en la
tienda.
"""
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from category.models import Category, CategoryAttribute

from .admin_attributes_api import AdminAttributeSerializer
from .models import (
    Attribute, AttributeKind, AttributeValue, GalleryProduct, Product,
    ProductAttributeValue,
)


def _parse_numeric(texto):
    """Decimal del texto que escribio el staff, o `None` si no es un numero.

    Acepta la coma decimal: en es-CL se escribe 3,5 y no 3.5.
    """
    try:
        return Decimal(texto.replace(',', '.'))
    except (InvalidOperation, AttributeError):
        return None


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


class AdminCategoryAttributeSerializer(serializers.ModelSerializer):
    """Enganche categoría↔atributo, con el atributo expandido para la app."""
    attribute = AdminAttributeSerializer(read_only=True)
    attribute_id = serializers.PrimaryKeyRelatedField(
        queryset=Attribute.objects.all(), source='attribute', write_only=True,
    )
    # De qué categoría viene: `null` si es propio, el nombre de la ancestra si
    # se hereda. La app usa esto para mostrar los heredados en gris y no
    # ofrecer borrarlos desde la hija.
    inherited_from = serializers.SerializerMethodField()

    class Meta:
        model = CategoryAttribute
        fields = [
            'id', 'attribute', 'attribute_id', 'is_required', 'sort_order',
            'inherited_from',
        ]

    def get_inherited_from(self, obj):
        target = self.context.get('category')
        if target is None or obj.category_id == target.pk:
            return None
        return {'id': obj.category_id, 'name': obj.category.name}


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

    @action(detail=True, methods=['get', 'post'], url_path='attributes')
    def attributes(self, request, pk=None):
        """Lista los atributos que aplican a la categoría, o engancha uno nuevo.

        El GET devuelve propios **y** heredados de las ancestras ya resueltos:
        "Anillos" hereda Material de "Joyas" sin que nadie lo repita. El POST
        siempre crea el enganche en *esta* categoría.
        """
        category = self.get_object()
        if request.method == 'GET':
            serializer = AdminCategoryAttributeSerializer(
                category.effective_attributes(), many=True,
                context={**self.get_serializer_context(), 'category': category},
            )
            return Response(serializer.data)
        serializer = AdminCategoryAttributeSerializer(
            data=request.data,
            context={**self.get_serializer_context(), 'category': category},
        )
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(category=category)
        except IntegrityError:
            return Response(
                {'detail': f'"{category.name}" ya tiene ese atributo.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'],
            url_path=r'attributes/(?P<attribute_id>\d+)')
    def attribute(self, request, pk=None, attribute_id=None):
        """Cambia (obligatorio/orden) o desengancha un atributo de la categoría.

        Solo alcanza a los enganches **propios**: un heredado se edita en la
        categoría que lo definió, si no una hija podría romperle la
        configuración a la madre y a todas sus hermanas.
        """
        category = self.get_object()
        link = CategoryAttribute.objects.filter(
            category=category, attribute_id=attribute_id,
        ).select_related('attribute').first()
        if link is None:
            inherited = any(
                item.attribute_id == int(attribute_id)
                for item in category.effective_attributes()
            )
            detail = (
                f'Ese atributo lo hereda "{category.name}" de una categoría '
                'madre: editalo ahí.'
            ) if inherited else 'Esta categoría no tiene ese atributo.'
            return Response({'detail': detail}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'DELETE':
            link.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AdminCategoryAttributeSerializer(
            link, data=request.data, partial=True,
            context={**self.get_serializer_context(), 'category': category},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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

    @action(detail=True, methods=['put', 'patch', 'delete'],
            url_path=r'images/(?P<image_id>\d+)')
    def gallery_image(self, request, pk=None, image_id=None):
        """Reemplaza (PUT/PATCH multipart, campo `images`) o borra una imagen.

        El reemplazo existe para el recorte desde la app: al editar una foto de
        la galería, el recorte queda EN SU LUGAR, sin sumar una foto nueva ni
        mover la posición que ya tenía en la lista.
        """
        product = self.get_object()
        image = GalleryProduct.objects.filter(product=product, id=image_id).first()
        if image is None:
            return Response(
                {'error': 'Imagen no encontrada en este producto.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == 'DELETE':
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        photo = request.FILES.get('images') or request.FILES.get('photos')
        if photo is None:
            return Response(
                {'error': 'Adjunta la imagen nueva en el campo `images`.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        image.photos = photo
        image.save()
        return Response(
            AdminGalleryImageSerializer(image).data, status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get', 'put'], url_path='attributes')
    def attribute_values(self, request, pk=None):
        """Ficha de atributos del producto: qué aplica y qué valor tiene.

        El GET devuelve **un renglón por atributo que aplica** (los de su
        categoría, propios y heredados), con `value` en `null` si todavía no se
        cargó. Así la app arma el formulario sin cruzar dos endpoints.

        El PUT recibe `{"values": [{"attribute_id": N, ...}, ...]}` y toca
        **solo los atributos nombrados**: los que no vienen quedan como están.
        Según el `kind` del atributo:

        - `select` → `value_id`, un `AttributeValue` de ese atributo.
        - `text`/`integer`/`decimal` → `value`, el texto que escribió el staff;
          se reutiliza el `AttributeValue` con ese texto o se crea.

        `value_id: null` o `value: ""` borra el valor cargado.

        Un producto lleva **un** valor por atributo: cargar otro reemplaza al
        anterior. Las variantes (mismo modelo en varias tallas, con stock por
        talla) quedan fuera: acá cada pieza es única y su talla es un dato de
        la pieza.
        """
        product = self.get_object()
        aplicables = {
            link.attribute_id: link
            for link in product.category.effective_attributes()
        } if product.category_id else {}

        if request.method == 'PUT':
            error = self._save_attribute_values(product, request.data, aplicables)
            if error is not None:
                return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        cargados = {
            pav.attribute_value.attribute_id: pav.attribute_value
            for pav in product.attribute_values.select_related(
                'attribute_value__attribute',
            )
        }
        return Response([
            {
                'attribute': AdminAttributeSerializer(link.attribute).data,
                'is_required': link.is_required,
                'inherited_from': (
                    None if link.category_id == product.category_id
                    else {'id': link.category_id, 'name': link.category.name}
                ),
                'value_id': cargados[attr_id].id if attr_id in cargados else None,
                'value': cargados[attr_id].value if attr_id in cargados else None,
            }
            for attr_id, link in aplicables.items()
        ])

    @staticmethod
    def _save_attribute_values(product, data, aplicables):
        """Aplica el PUT. Devuelve el mensaje de error, o `None` si salió bien.

        Valida todo antes de escribir: media ficha guardada es peor que un 400.
        """
        entradas = data.get('values')
        if not isinstance(entradas, list):
            return 'Mandá `values` con la lista de atributos a guardar.'

        pendientes = []
        for entrada in entradas:
            if not isinstance(entrada, dict):
                return 'Cada elemento de `values` tiene que ser un objeto.'
            attr_id = entrada.get('attribute_id')
            link = aplicables.get(attr_id)
            if link is None:
                return (
                    'Ese atributo no aplica a la categoría del producto. '
                    'Enganchalo a la categoría primero.'
                )
            attribute = link.attribute

            if attribute.kind == AttributeKind.SELECT:
                value_id = entrada.get('value_id')
                if value_id in (None, ''):
                    pendientes.append((attribute, None))
                    continue
                value = AttributeValue.objects.filter(
                    attribute=attribute, id=value_id,
                ).first()
                if value is None:
                    return f'Ese valor no pertenece a "{attribute.name}".'
                pendientes.append((attribute, value))
                continue

            texto = entrada.get('value')
            texto = '' if texto is None else str(texto).strip()
            if not texto:
                pendientes.append((attribute, None))
                continue
            numero = _parse_numeric(texto)
            if attribute.kind == AttributeKind.INTEGER and (
                numero is None or numero != numero.to_integral_value()
            ):
                return f'"{attribute.name}" lleva un número entero.'
            if attribute.kind == AttributeKind.DECIMAL and numero is None:
                return f'"{attribute.name}" lleva un número (ej. 3,5).'
            pendientes.append((attribute, (texto, numero)))

        for attribute, destino in pendientes:
            # Un valor por atributo: lo viejo se va, venga lo que venga.
            ProductAttributeValue.objects.filter(
                product=product, attribute_value__attribute=attribute,
            ).delete()
            if destino is None:
                continue
            if isinstance(destino, tuple):
                texto, numero = destino
                # Los valores libres tambien viven en `AttributeValue`: el
                # modelo no guarda texto suelto en el producto. Se reutiliza el
                # que ya exista para no llenar la tabla de duplicados.
                destino, _ = AttributeValue.objects.get_or_create(
                    attribute=attribute, value=texto,
                    defaults={'numeric_value': numero},
                )
            ProductAttributeValue.objects.create(
                product=product, attribute_value=destino,
            )
        return None

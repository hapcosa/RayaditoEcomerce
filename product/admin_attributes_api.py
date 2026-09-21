"""API de escritura de atributos para staff (app admin Expo). Montada en /api/admin/.

Un `Attribute` es una definición reutilizable: "Talla", "Color", "Métrica
europea", "Alto". `kind` decide cómo se carga el valor en el producto:

- `select`   → el atributo trae su propia enumeración de `AttributeValue`
               ("Métrica europea" con 16, 17, 18…). Es el único kind con valores.
- `integer` / `decimal` / `text` → el valor lo escribe el staff producto por
               producto (alto/ancho/largo de una piedra), no hay lista fija.

`is_variant_option` separa lo que genera stock de lo que es ficha técnica: una
talla produce `ProductVariant` comprables con stock propio, un alto en cm no.
Solo tiene sentido en `select` (ver `AdminAttributeSerializer.validate`).

Todo requiere `IsAdminUser` (== `is_staff`).
"""
from django.db import IntegrityError
from django.utils.text import slugify
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Attribute, AttributeKind, AttributeValue


class AdminAttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ['id', 'value', 'numeric_value', 'sort_order']

    def validate_value(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El valor no puede quedar vacío.')
        return value


class AdminAttributeSerializer(serializers.ModelSerializer):
    # `slug` se deriva del nombre: la app manda "Métrica europea" y no tiene por
    # qué saber de slugs.
    slug = serializers.SlugField(read_only=True)
    values = AdminAttributeValueSerializer(many=True, read_only=True)
    # Cuántos productos/variantes lo usan: la app lo muestra y lo usa para
    # avisar antes de intentar borrar.
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = [
            'id', 'name', 'slug', 'unit', 'kind', 'is_variant_option',
            'sort_order', 'values', 'usage_count',
        ]

    def get_usage_count(self, obj):
        return AttributeValue.objects.filter(attribute=obj).filter(
            products__isnull=False,
        ).count() + AttributeValue.objects.filter(attribute=obj).filter(
            variants__isnull=False,
        ).count()

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Poné un nombre (ej. Talla, Color).')
        return value

    def validate(self, attrs):
        kind = attrs.get('kind', getattr(self.instance, 'kind', AttributeKind.SELECT))
        is_variant = attrs.get(
            'is_variant_option', getattr(self.instance, 'is_variant_option', False),
        )
        if is_variant and kind != AttributeKind.SELECT:
            raise serializers.ValidationError({
                'is_variant_option': (
                    'Solo un atributo de selección puede generar variantes: una '
                    'medida libre no define stock comprable.'
                ),
            })
        return attrs

    def create(self, validated_data):
        validated_data['slug'] = self._unique_slug(validated_data['name'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Renombrar no re-slugifica: el slug ya puede estar referenciado desde
        # el front público (`/api/attributes/`).
        return super().update(instance, validated_data)

    @staticmethod
    def _unique_slug(name):
        base = slugify(name) or 'atributo'
        candidate = base[:120]
        suffix = 2
        while Attribute.objects.filter(slug=candidate).exists():
            tail = f'-{suffix}'
            candidate = f'{base[:120 - len(tail)]}{tail}'
            suffix += 1
        return candidate


class AdminAttributeViewSet(viewsets.ModelViewSet):
    """CRUD de atributos + su enumeración de valores."""
    queryset = Attribute.objects.prefetch_related('values').order_by(
        'sort_order', 'name',
    )
    serializer_class = AdminAttributeSerializer
    permission_classes = (IsAdminUser,)
    pagination_class = None

    def destroy(self, request, *args, **kwargs):
        """Borra solo si nadie lo usa.

        `AttributeValue` cae en CASCADE desde `Attribute`, y de ahí se llevaría
        por delante los `ProductAttributeValue` y las variantes que lo usen:
        borrar "Talla" de un tap dejaría productos sin su talla y sin stock.
        """
        attribute = self.get_object()
        in_use = AttributeValue.objects.filter(attribute=attribute).filter(
            products__isnull=False,
        ).exists() or AttributeValue.objects.filter(attribute=attribute).filter(
            variants__isnull=False,
        ).exists()
        if in_use:
            return Response(
                {'detail': (
                    'No se puede borrar: hay productos o variantes usando este '
                    'atributo. Quitalo de esos productos primero.'
                )},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='values')
    def add_value(self, request, pk=None):
        """Agrega un valor a la enumeración (ej. la talla 42 a Métrica europea)."""
        attribute = self.get_object()
        if attribute.kind != AttributeKind.SELECT:
            return Response(
                {'detail': (
                    f'"{attribute.name}" es de tipo {attribute.get_kind_display()}: '
                    'su valor se escribe en cada producto, no tiene lista fija.'
                )},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AdminAttributeValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            value = serializer.save(attribute=attribute)
        except IntegrityError:
            return Response(
                {'detail': f'"{attribute.name}" ya tiene ese valor.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            AdminAttributeValueSerializer(value).data, status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['put', 'patch', 'delete'],
            url_path=r'values/(?P<value_id>\d+)')
    def value(self, request, pk=None, value_id=None):
        """Edita o borra un valor concreto de la enumeración."""
        attribute = self.get_object()
        value = AttributeValue.objects.filter(
            attribute=attribute, id=value_id,
        ).first()
        if value is None:
            return Response(
                {'detail': 'Ese valor no pertenece a este atributo.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'DELETE':
            if value.products.exists() or value.variants.exists():
                return Response(
                    {'detail': (
                        'No se puede borrar: hay productos o variantes con este '
                        'valor. Cambialos primero.'
                    )},
                    status=status.HTTP_409_CONFLICT,
                )
            value.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AdminAttributeValueSerializer(
            value, data=request.data, partial=request.method == 'PATCH',
        )
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {'detail': f'"{attribute.name}" ya tiene ese valor.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(serializer.data, status=status.HTTP_200_OK)

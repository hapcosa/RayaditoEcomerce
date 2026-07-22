from rest_framework import serializers
from .models import (
    Attribute,
    AttributeValue,
    Product,
    ProductAttributeValue,
    ProductVariant,
    Joyas,
    Piedras,
    GalleryProduct,
    Review,
)


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_slug = serializers.CharField(source='attribute.slug', read_only=True)
    unit = serializers.CharField(source='attribute.unit', read_only=True)
    kind = serializers.CharField(source='attribute.kind', read_only=True)

    class Meta:
        model = AttributeValue
        fields = [
            'id', 'attribute', 'attribute_name', 'attribute_slug',
            'value', 'numeric_value', 'unit', 'kind',
        ]


class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = [
            'id', 'name', 'slug', 'unit', 'kind', 'is_variant_option',
            'sort_order', 'values',
        ]


class GalleryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=GalleryProduct
        fields = '__all__'


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='attribute_value.id', read_only=True)
    attribute = serializers.IntegerField(source='attribute_value.attribute_id', read_only=True)
    attribute_name = serializers.CharField(source='attribute_value.attribute.name', read_only=True)
    attribute_slug = serializers.CharField(source='attribute_value.attribute.slug', read_only=True)
    unit = serializers.CharField(source='attribute_value.attribute.unit', read_only=True)
    kind = serializers.CharField(source='attribute_value.attribute.kind', read_only=True)
    value = serializers.CharField(source='attribute_value.value', read_only=True)
    numeric_value = serializers.DecimalField(
        source='attribute_value.numeric_value',
        max_digits=10,
        decimal_places=3,
        read_only=True,
    )

    class Meta:
        model = ProductAttributeValue
        fields = [
            'id', 'attribute', 'attribute_name', 'attribute_slug',
            'value', 'numeric_value', 'unit', 'kind',
        ]


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)
    effective_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price_override', 'effective_price',
            'stock', 'is_active', 'attributes',
        ]


class ProductSerializer(serializers.ModelSerializer):
    attributes = ProductAttributeValueSerializer(
        source='attribute_values', many=True, read_only=True,
    )
    variants = ProductVariantSerializer(many=True, read_only=True)
    gallery = GalleryProductSerializer(
        source='galleryproduct_set', many=True, read_only=True,
    )
    available_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model=Product
        fields = [
            'id', 'name', 'slug', 'product_type', 'photo', 'description',
            'price', 'compare_price', 'category', 'sold', 'status',
            'is_featured', 'date_created', 'available_stock',
            'attributes', 'variants', 'gallery',
        ]


class JoyasSerializer(serializers.ModelSerializer):
    class Meta:
        model=Joyas
        fields = '__all__'


class PiedrasSerializer(serializers.ModelSerializer):
    class Meta:
        model=Piedras
        fields = '__all__'
class RelationPiedraJoyaSerializer(serializers.ModelSerializer):
    class Meta:
        model=GalleryProduct
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'user_name', 'rating', 'comment',
                  'verified_purchase', 'approved', 'created_at', 'updated_at']
        read_only_fields = ['product', 'user', 'user_name', 'verified_purchase',
                            'approved', 'created_at', 'updated_at']

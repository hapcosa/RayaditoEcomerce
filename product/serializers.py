from rest_framework import serializers
from .models import Product, Joyas, Piedras, GalleryProduct, Review

class JoyasSerializer(serializers.ModelSerializer):
    class Meta:
        model=Joyas
        fields = '__all__'
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields = '__all__'
class PiedrasSerializer(serializers.ModelSerializer):
    class Meta:
        model=Piedras
        fields = '__all__'
class GalleryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=GalleryProduct
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

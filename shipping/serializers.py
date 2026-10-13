from rest_framework import serializers
from .models import Shipping


class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'


def serialize_priced(priced):
    """Opciones con el precio ya calculado (cotizado o fijo) en `price`."""
    data = []
    for shipping, price in priced:
        item = ShippingSerializer(shipping).data
        item['price'] = price
        data.append(item)
    return data


class ShippingQuoteRequestSerializer(serializers.Serializer):
    region = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    city = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    comuna = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        destination_fields = ('region', 'city', 'comuna')
        if not any(attrs.get(field) for field in destination_fields):
            raise serializers.ValidationError(
                'Debe indicar region, city o comuna para cotizar el envio.'
            )
        return attrs

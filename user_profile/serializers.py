from rest_framework import serializers

from .models import UserProfile


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id', 'label', 'first_name', 'last_name', 'address_line_1',
            'city', 'country_region', 'zipcode', 'phone', 'is_default',
        ]

    def validate_first_name(self, value):
        return self._obligatorio(value, 'Indicá el nombre de quien recibe.')

    def validate_last_name(self, value):
        return self._obligatorio(value, 'Indicá el apellido de quien recibe.')

    def validate_address_line_1(self, value):
        return self._obligatorio(value, 'Indicá calle y número.')

    def validate_city(self, value):
        return self._obligatorio(value, 'Indicá la ciudad o comuna.')

    def validate_country_region(self, value):
        return self._obligatorio(value, 'Indicá la región.')

    def validate_phone(self, value):
        return self._obligatorio(value, 'Indicá un teléfono de contacto.')

    @staticmethod
    def _obligatorio(value, mensaje):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError(mensaje)
        return value

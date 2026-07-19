from rest_framework import serializers

from .models import Suggestion


class SuggestionCreateSerializer(serializers.ModelSerializer):
    """Entrada pública: solo los campos que aporta quien escribe."""

    class Meta:
        model = Suggestion
        fields = ('name', 'email', 'kind', 'message')

    def validate_message(self, value):
        value = (value or '').strip()
        if len(value) < 3:
            raise serializers.ValidationError('El mensaje es demasiado corto.')
        return value


class SuggestionSerializer(serializers.ModelSerializer):
    """Salida (admin): incluye estado, autor enlazado y fecha."""

    user_email = serializers.EmailField(source='user.email', read_only=True, default=None)

    class Meta:
        model = Suggestion
        fields = ('id', 'name', 'email', 'kind', 'message', 'status',
                  'user', 'user_email', 'created_at')
        read_only_fields = fields

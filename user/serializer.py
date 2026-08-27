from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()

class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'get_full_name',
            'get_short_name'
        )


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serializer para /auth/users/me/ y detalle de usuario.

    Expone `is_staff`/`is_superuser` en solo-lectura para que la app admin
    verifique permisos. NUNCA se usa para crear/registrar: esos flags no
    deben ser escribibles desde el registro público.
    """

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'get_full_name',
            'get_short_name',
            'is_staff',
            'is_superuser',
        )
        read_only_fields = fields
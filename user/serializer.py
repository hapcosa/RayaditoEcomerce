from djoser.serializers import UserCreateSerializer
from djoser.social.serializers import ProviderAuthSerializer as DjoserProviderAuthSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from social_core import exceptions as social_exceptions
from social_django.utils import load_backend, load_strategy
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

class ProviderAuthSerializer(DjoserProviderAuthSerializer):
    """Cierre del login social (`POST /auth/o/{provider}/`).

    Djoser valida el `state` en un paso aparte y después llama a
    `auth_complete()`, que lo vuelve a validar. Desde social-auth-core 6 el
    `state` es de un solo uso: el primer chequeo lo consume y el segundo falla
    con "authentication session is unavailable". Acá se valida una sola vez,
    dentro de `auth_complete()`, que además rechaza un `state` ausente.
    """

    def validate(self, attrs):
        request = self.context['request']
        strategy = load_strategy(request)
        redirect_uri = strategy.session_get('redirect_uri')
        backend_name = self.context['view'].kwargs['provider']
        backend = load_backend(strategy, backend_name, redirect_uri=redirect_uri)

        try:
            user = backend.auth_complete()
        except social_exceptions.AuthException as e:
            raise serializers.ValidationError(str(e))
        except (ConnectionError, OSError) as e:
            raise serializers.ValidationError(
                f'Network error during authentication: {e}'
            )
        return {'user': user}

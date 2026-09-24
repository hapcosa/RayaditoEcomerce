from django.contrib import admin

from .models import DevicePushToken


@admin.register(DevicePushToken)
class DevicePushTokenAdmin(admin.ModelAdmin):
    """Solo lectura: los tokens los registra la app, no se escriben a mano."""
    list_display = ('user', 'platform', 'is_active', 'updated_at', 'last_error')
    list_filter = ('is_active', 'platform')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'user', 'platform', 'created_at', 'updated_at',
                       'last_error')

    def has_add_permission(self, request):
        return False

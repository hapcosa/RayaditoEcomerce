from django.contrib import admin

from .models import DevicePushToken, WhatsAppMessage, WhatsAppOptIn


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


@admin.register(WhatsAppOptIn)
class WhatsAppOptInAdmin(admin.ModelAdmin):
    """Lo crea el checkout. Desde aqui solo se registra la baja (`revoked_at`)."""
    list_display = ('order', 'phone', 'created_at', 'revoked_at')
    list_filter = ('revoked_at',)
    search_fields = ('phone', 'order__id', 'order__email')
    readonly_fields = ('order', 'phone', 'consent_text', 'created_at')

    def has_add_permission(self, request):
        return False


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('order', 'key', 'template', 'status', 'created_at', 'error')
    list_filter = ('status', 'key')
    search_fields = ('order__id', 'to', 'wamid')
    readonly_fields = ('order', 'key', 'template', 'to', 'status', 'wamid',
                       'error', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

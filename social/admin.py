from django.contrib import admin

from .models import InstagramPost, InstagramToken


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ('product', 'status', 'scheduled_for', 'published_at', 'attempts')
    list_filter = ('status',)
    search_fields = ('product__name', 'caption')
    readonly_fields = ('media_id', 'permalink', 'last_error', 'attempts',
                       'created_by', 'created_at', 'started_at', 'published_at')


@admin.register(InstagramToken)
class InstagramTokenAdmin(admin.ModelAdmin):
    # El token cifrado no se muestra: se carga con `manage.py instagram_token set`.
    list_display = ('issued_at', 'expires_at', 'last_refresh_attempt', 'last_error')
    fields = ('issued_at', 'expires_at', 'last_refresh_attempt', 'last_error')
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

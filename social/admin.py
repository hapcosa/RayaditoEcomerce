from django.contrib import admin

from .models import InstagramPost


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ('product', 'status', 'scheduled_for', 'published_at', 'attempts')
    list_filter = ('status',)
    search_fields = ('product__name', 'caption')
    readonly_fields = ('media_id', 'permalink', 'last_error', 'attempts',
                       'created_by', 'created_at', 'started_at', 'published_at')

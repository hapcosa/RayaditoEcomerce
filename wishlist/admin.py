from django.contrib import admin

from .models import WishlistItem


class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'created_at')
    list_display_links = ('id',)
    list_filter = ('created_at',)
    search_fields = ('user__email', 'product__name')
    raw_id_fields = ('user', 'product')
    list_per_page = 25


admin.site.register(WishlistItem, WishlistItemAdmin)

from django.contrib import admin
from .models import Carrito, CarritoItem


class CarritoItemInline(admin.TabularInline):
    model = CarritoItem
    extra = 0


class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items')
    list_display_links = ('id', 'user')
    search_fields = ('user__email',)
    inlines = (CarritoItemInline,)
    list_per_page = 25


class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrito', 'product', 'count')
    list_display_links = ('id',)
    list_filter = ('carrito',)
    search_fields = ('product__name',)
    list_per_page = 25


admin.site.register(Carrito, CarritoAdmin)
admin.site.register(CarritoItem, CarritoItemAdmin)

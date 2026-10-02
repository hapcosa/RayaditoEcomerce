from django.contrib import admin
from .models import Shipment, Shipping


class ShippingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'carrier', 'starken_delivery_type', 'price', )
    list_display_links = ('name', )
    list_editable = ('price', )
    list_filter = ('carrier', )
    search_fields = ('name', )
    list_per_page = 25


class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'tracking_number', 'status', 'status_at', 'is_final', 'last_error')
    list_filter = ('is_final', 'carrier')
    search_fields = ('tracking_number', 'order__id')
    readonly_fields = ('created_at', )
    raw_id_fields = ('order', )


admin.site.register(Shipping, ShippingAdmin)
admin.site.register(Shipment, ShipmentAdmin)

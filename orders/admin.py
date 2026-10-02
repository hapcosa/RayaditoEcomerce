from django.contrib import admin
from .models import Order, OrderItem, WithdrawalRequest
# Register your models here.


class OrderAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'transaction_id', 'amount', 'shipping_price', 'status', 'deliveryNumber', )
    list_display_links = ('id', 'transaction_id', )
    list_filter = ('status', )
    list_editable = ('status', )
    search_fields = ('id', 'transaction_id', 'deliveryNumber', 'email', )
    list_per_page = 25

admin.site.register(Order, OrderAdmin)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', )
    list_display_links = ('id', 'name', )
    list_per_page = 25


admin.site.register(OrderItem, OrderItemAdmin)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('code', 'order', 'email', 'status', 'created_at', 'resolved_at')
    list_filter = ('status',)
    search_fields = ('code', 'email', 'order__id', 'order__transaction_id')
    readonly_fields = ('code', 'order', 'email', 'reason', 'created_at')

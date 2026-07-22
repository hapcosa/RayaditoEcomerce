from django.contrib import admin
from .models import Payments
# Register your models here.


class PaymentsAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'payment_id', 'order', 'status', 'payment_method_id',
        'typepayment', 'cuotas', 'stock_deducted', 'updated_at',
    )
    list_display_links = ('id', 'payment_id')
    list_filter = ('status', 'typepayment', 'cuotas', 'stock_deducted')
    search_fields = ('=payment_id', 'external_reference', '=order__id')
    readonly_fields = ('raw_response', 'created_at', 'updated_at')


admin.site.register(Payments, PaymentsAdmin)

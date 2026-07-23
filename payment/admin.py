from django.contrib import admin
from django.contrib import messages
from .models import Payments
from .services import MercadoPagoConfigurationError, sync_payment
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
    actions = ('sync_with_mercadopago',)

    @admin.action(description='Conciliar seleccionados con MercadoPago')
    def sync_with_mercadopago(self, request, queryset):
        synced = 0
        failures = 0
        for payment in queryset:
            try:
                sync_payment(payment.payment_id)
            except MercadoPagoConfigurationError as exc:
                self.message_user(request, str(exc), messages.ERROR)
                return
            except Exception:
                failures += 1
                continue
            synced += 1

        if failures:
            self.message_user(
                request,
                f'{synced} pago(s) conciliado(s), {failures} con error.',
                messages.WARNING,
            )
            return

        self.message_user(request, f'{synced} pago(s) conciliado(s).', messages.SUCCESS)


admin.site.register(Payments, PaymentsAdmin)

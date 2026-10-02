from django.contrib import admin

from .models import InvoiceRequest, TaxDocument


@admin.register(TaxDocument)
class TaxDocumentAdmin(admin.ModelAdmin):
    """Editable a proposito: una factura emitida a mano en el portal del SII
    se registra aca cargando el folio y pasandola a "Emitido"."""
    list_display = ('order', 'kind', 'status', 'folio', 'amount', 'provider', 'issued_at')
    list_filter = ('status', 'kind', 'provider')
    search_fields = ('order__id', 'order__transaction_id', 'folio', 'external_id')
    readonly_fields = ('order', 'kind', 'amount', 'created_at', 'last_error')


@admin.register(InvoiceRequest)
class InvoiceRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'rut', 'business_name', 'commune', 'created_at')
    search_fields = ('rut', 'business_name', 'order__id')
    readonly_fields = ('order', 'created_at')

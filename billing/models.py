from django.db import models


class InvoiceRequest(models.Model):
    """Datos de facturacion que el cliente pidio en el checkout.

    Sin esto la venta va con boleta (o con el comprobante de pago, que el SII
    reconoce como boleta). Solo se pide si BILLING_INVOICES_ENABLED.
    """

    order = models.OneToOneField(
        'orders.Order', on_delete=models.CASCADE, related_name='invoice_request',
    )
    rut = models.CharField(max_length=12)
    business_name = models.CharField('razon social', max_length=255)
    activity = models.CharField('giro', max_length=255)
    address = models.CharField(max_length=255)
    commune = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'datos de factura'
        verbose_name_plural = 'datos de factura'

    def __str__(self):
        return f'{self.business_name} ({self.rut}) · pedido {self.order_id}'


class TaxDocument(models.Model):
    """El documento tributario de una venta: que se emitio, o que falta emitir.

    Hay a lo mas uno por pedido y tipo. Un `PENDING` es trabajo pendiente para la tienda
    (emitirlo en el portal del SII y cargar el folio) o para el proveedor
    configurado; un `ISSUED` ya esta resuelto.
    """

    class Kind(models.TextChoices):
        # Comprobante de pago electronico de MercadoPago: vale como boleta
        # (Res. Ex. SII N° 176 de 2020). No se emite nada aparte.
        VOUCHER = 'voucher', 'Comprobante de pago (vale como boleta)'
        BOLETA = 'boleta', 'Boleta electrónica'
        FACTURA = 'factura', 'Factura electrónica'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        ISSUED = 'issued', 'Emitido'
        FAILED = 'failed', 'Falló'

    order = models.ForeignKey(
        'orders.Order', on_delete=models.PROTECT, related_name='tax_documents',
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    # Quien lo emitio: 'mercadopago', 'manual' (portal del SII) o el nombre del
    # proveedor configurado.
    provider = models.CharField(max_length=40, blank=True, default='')
    folio = models.CharField(max_length=40, blank=True, default='')
    external_id = models.CharField(max_length=120, blank=True, default='')
    pdf_url = models.URLField(blank=True, default='')
    # Total del documento en entero CLP, con IVA incluido (ver AGENTS.md).
    amount = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'documento tributario'
        verbose_name_plural = 'documentos tributarios'
        constraints = [
            models.UniqueConstraint(fields=['order', 'kind'],
                                    name='one_tax_document_per_order_and_kind'),
        ]

    def __str__(self):
        folio = f' N° {self.folio}' if self.folio else ''
        return f'{self.get_kind_display()}{folio} · pedido {self.order_id}'

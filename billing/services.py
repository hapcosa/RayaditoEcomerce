"""Documento tributario de cada venta pagada.

Modos (BILLING_MODE):

- 'off': sin inicio de actividades. No se registra nada.
- 'voucher': el comprobante de pago de MercadoPago vale como boleta (Res. Ex.
  SII N° 176 de 2020), asi que una venta normal no requiere emitir nada: solo
  se deja constancia. Las facturas quedan pendientes para emitirlas a mano en
  el portal del SII y se avisa por correo al admin.
- 'provider': boletas y facturas las emite un proveedor externo por API.

Igual que los avisos, nada de esto puede tumbar el pago: corre despues del
commit y los errores quedan en el documento (`FAILED`), no en el webhook.
"""
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from notifications.services import order_admin_url, send_admin_mail
from orders.models import OrderItem

from . import rut as rut_utils
from .models import InvoiceRequest, TaxDocument
from .providers import BillingError, get_provider

logger = logging.getLogger(__name__)

MODES = ('off', 'voucher', 'provider')


def mode():
    value = (settings.BILLING_MODE or 'off').strip().lower()
    return value if value in MODES else 'off'


def invoices_enabled():
    return mode() != 'off' and settings.BILLING_INVOICES_ENABLED


def parse_invoice_request(data):
    """Valida los datos de factura del checkout.

    Devuelve `(datos, None)`, `(None, None)` si no se pidio factura, o
    `(None, errores)` si los datos no sirven.
    """
    if not data or not invoices_enabled():
        return None, None
    if not isinstance(data, dict):
        return None, {'invoice': 'Datos de factura inválidos.'}

    errors = {}
    rut = rut_utils.normalize(str(data.get('rut') or ''))
    if not rut:
        errors['rut'] = 'RUT inválido.'
    cleaned = {'rut': rut}
    for field, label, limit in (
        ('business_name', 'la razón social', 255),
        ('activity', 'el giro', 255),
        ('address', 'la dirección', 255),
        ('commune', 'la comuna', 120),
    ):
        value = str(data.get(field) or '').strip()
        if not value:
            errors[field] = f'Falta {label}.'
        cleaned[field] = value[:limit]
    cleaned['email'] = str(data.get('email') or '').strip()[:254]
    if errors:
        return None, errors
    return cleaned, None


def attach_invoice_request(order, data):
    if data:
        InvoiceRequest.objects.update_or_create(order=order, defaults=data)


def _issue_with_provider(document):
    order = document.order
    items = list(OrderItem.objects.filter(order=order))
    invoice = InvoiceRequest.objects.filter(order=order).first()
    try:
        provider = get_provider()
        issued = provider.issue(document, order, items, invoice=invoice)
    except Exception as exc:
        # Ancho a proposito: un proveedor mal configurado o caido no puede
        # tumbar nada. El documento queda FAILED y el comando lo reintenta.
        if not isinstance(exc, BillingError):
            logger.exception('error inesperado emitiendo %s', document)
        document.status = TaxDocument.Status.FAILED
        document.last_error = str(exc)[:2000]
        document.save(update_fields=['status', 'last_error'])
        return False

    document.status = TaxDocument.Status.ISSUED
    document.provider = provider.name or settings.BILLING_PROVIDER
    document.folio = issued.folio
    document.external_id = issued.external_id
    document.pdf_url = issued.pdf_url
    document.last_error = ''
    document.issued_at = timezone.now()
    document.save()
    return True


def on_order_paid(order):
    """Registra (y si corresponde emite) el documento de una venta pagada."""
    current = mode()
    if current == 'off':
        return None

    invoice = InvoiceRequest.objects.filter(order=order).first()
    if invoice:
        kind = TaxDocument.Kind.FACTURA
    elif current == 'voucher':
        kind = TaxDocument.Kind.VOUCHER
    else:
        kind = TaxDocument.Kind.BOLETA

    document, created = TaxDocument.objects.get_or_create(
        order=order, kind=kind, defaults={'amount': order.amount or 0},
    )
    if not created:
        # MercadoPago reenvia la misma aprobacion: el documento ya existe.
        return document

    if kind == TaxDocument.Kind.VOUCHER:
        document.status = TaxDocument.Status.ISSUED
        document.provider = 'mercadopago'
        document.external_id = order.transaction_id or ''
        document.issued_at = timezone.now()
        document.save()
    elif current == 'provider':
        _issue_with_provider(document)
    else:
        document.provider = 'manual'
        document.save(update_fields=['provider'])
        send_admin_mail(
            subject=f'Factura por emitir — pedido #{order.id}',
            template='billing/admin_invoice_pending.txt',
            context={'order': order, 'invoice': invoice, 'document': document,
                     'rut': rut_utils.pretty(invoice.rut),
                     'admin_url': order_admin_url(order)},
        )
    return document


def on_order_paid_on_commit(order):
    def run():
        try:
            on_order_paid(order)
        except Exception:
            logger.exception('no se pudo registrar el documento tributario del pedido %s',
                             order.id)
    transaction.on_commit(run)


def retry_failed(limit=50):
    """Reintenta con el proveedor los documentos que fallaron. Solo modo 'provider'."""
    if mode() != 'provider':
        return 0, 0
    documents = list(
        TaxDocument.objects
        .filter(status__in=(TaxDocument.Status.FAILED, TaxDocument.Status.PENDING),
                kind__in=(TaxDocument.Kind.BOLETA, TaxDocument.Kind.FACTURA))
        .exclude(provider='manual')
        .select_related('order')
        .order_by('created_at')[:limit]
    )
    issued = sum(1 for document in documents if _issue_with_provider(document))
    return issued, len(documents)

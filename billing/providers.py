"""Interfaz para emitir boletas y facturas con un proveedor externo.

No hay ningun proveedor implementado todavia: depende de cual se contrate
(OpenFactura, SimpleAPI, LibreDTE, Bsale...). Para conectar uno se escribe una
subclase de `BillingProvider` en este paquete y se apunta BILLING_PROVIDER a
ella con su ruta, p. ej. `billing.providers.OpenFacturaProvider`. Ver
docs/SII.md.
"""
from typing import NamedTuple

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class BillingError(Exception):
    """El proveedor rechazo el documento o no respondio."""


class IssuedDocument(NamedTuple):
    folio: str
    external_id: str = ''
    pdf_url: str = ''


class BillingProvider:
    """Lo que tiene que saber hacer un proveedor de documentos tributarios."""

    #: Se guarda en TaxDocument.provider.
    name = ''

    def issue(self, document, order, items, invoice=None):
        """Emite el documento y devuelve sus datos, o levanta BillingError.

        `document.kind` es 'boleta' o 'factura'; `invoice` (InvoiceRequest)
        viene solo para facturas. Los montos son entero CLP con IVA incluido.
        Debe ser idempotente por `document.pk`: si se reintenta un documento
        que el proveedor ya emitio, tiene que devolver el mismo folio y no
        emitir otro.
        """
        raise NotImplementedError


def get_provider():
    path = settings.BILLING_PROVIDER
    if not path:
        raise ImproperlyConfigured(
            "BILLING_MODE='provider' necesita BILLING_PROVIDER (ver docs/SII.md)")
    return import_string(path)()

"""Configuracion publica de facturacion. Montada en /api/billing/.

El checkout la consulta para saber si ofrece "Necesito factura": antes del
inicio de actividades no hay a quien emitirsela.
"""
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import invoices_enabled, mode


class BillingConfigView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def get(self, request):
        return Response({'mode': mode(), 'invoices_enabled': invoices_enabled()})

import unicodedata

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .locations import CHILE_REGIONS, TOTAL_COMMUNES
from .models import Shipping
from .serializers import ShippingQuoteRequestSerializer, ShippingSerializer


def _normalize_location(value):
    normalized = unicodedata.normalize('NFKD', str(value or ''))
    without_accents = ''.join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.casefold().strip()


def _region_payload(region):
    return {
        **region,
        'communes_count': len(region['communes']),
    }


def _find_region(value):
    query = _normalize_location(value)
    for region in CHILE_REGIONS:
        aliases = (
            region['number'],
            region['roman'],
            region['name'],
        )
        if query in {_normalize_location(alias) for alias in aliases}:
            return region
    return None


class ChileShippingLocationsView(APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request, format=None):
        region_query = request.query_params.get('region')
        if region_query:
            region = _find_region(region_query)
            if not region:
                return Response(
                    {'error': 'Region no encontrada'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {'region': _region_payload(region)},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                'regions': [_region_payload(region) for region in CHILE_REGIONS],
                'count': len(CHILE_REGIONS),
                'total_communes': TOTAL_COMMUNES,
            },
            status=status.HTTP_200_OK,
        )


class GetShippingView(APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request, format=None):
        if Shipping.objects.all().exists():
            shipping_options = Shipping.objects.order_by('name').all()
            shipping_options = ShippingSerializer(shipping_options, many=True)

            return Response(
                {'shipping_options': shipping_options.data},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'No shipping options available'},
                status=status.HTTP_404_NOT_FOUND
            )


class QuoteShippingView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, format=None):
        serializer = ShippingQuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shipping_options = Shipping.objects.order_by('price', 'id')
        if not shipping_options.exists():
            return Response(
                {'error': 'No shipping options available'},
                status=status.HTTP_404_NOT_FOUND
            )

        destination = {
            key: value
            for key, value in serializer.validated_data.items()
            if value
        }

        return Response(
            {
                'source': 'manual',
                'destination': destination,
                'shipping_options': ShippingSerializer(shipping_options, many=True).data,
            },
            status=status.HTTP_200_OK
        )

class GetShippingOptionId(APIView):
     permission_classes = (permissions.AllowAny, )
     def get(self, request, ShippingId, format=None):
        try:
            shippingId=int(ShippingId)
        except:
            return Response(
                {'error': 'Error datos de envio no validos,\n recargue la pagina o contacte al administrador'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        if Shipping.objects.filter(id=shippingId).exists():
            shipping_option = Shipping.objects.get(id=shippingId)
            shipping_option = ShippingSerializer(shipping_option)

            return Response(
                {'shipping_option': shipping_option.data},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Opción de envio no valida'},
                status=status.HTTP_404_NOT_FOUND
            )

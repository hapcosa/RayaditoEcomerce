from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum

from .models import Carrito, CarritoItem
from product.models import Product
from product.serializers import ProductSerializer


def _serialize_cart(cart):
    """Items del carrito con id, count y producto (contrato del front)."""
    items = CarritoItem.objects.order_by('product').filter(carrito=cart)
    return [
        {
            'id': cart_item.id,
            'count': cart_item.count,
            'product': ProductSerializer(cart_item.product).data,
        }
        for cart_item in items
    ]


def _sync_total_items(cart):
    """total_items = suma de las cantidades de todos los items del carrito."""
    total = CarritoItem.objects.filter(carrito=cart).aggregate(
        n=Sum('count'))['n'] or 0
    Carrito.objects.filter(id=cart.id).update(total_items=total)
    return total


def _has_available_stock(product, count):
    if product.sold:
        return False
    variant_stock = product.variants.filter(is_active=True).aggregate(
        total=Sum('stock'))['total']
    if variant_stock is None:
        return True
    return variant_stock >= count


class GetItemsView(APIView):
    def get(self, request, format=None):
        try:
            cart = Carrito.objects.get(user=request.user)
            return Response({'cart': _serialize_cart(cart)}, status=status.HTTP_200_OK)
        except Carrito.DoesNotExist:
            return Response({'error': 'items no encontrados'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddItemView(APIView):
    def put(self, request, format=None):
        data = request.data
        try:
            product_id = int(data['product_id'])
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Product ID must be an integer'},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'producto no existe'},
                            status=status.HTTP_404_NOT_FOUND)

        cart = Carrito.objects.get(user=request.user)

        if CarritoItem.objects.filter(carrito=cart, product=product).exists():
            return Response(
                {'error': 'Este producto ya se ha agregado al carro de compras'},
                status=status.HTTP_409_CONFLICT)

        if not _has_available_stock(product, 1):
            return Response({'error': 'este producto ya no esta disponible'},
                            status=status.HTTP_200_OK)

        CarritoItem.objects.create(carrito=cart, product=product, count=1)
        _sync_total_items(cart)
        return Response({'cart': _serialize_cart(cart)}, status=status.HTTP_201_CREATED)


class GetTotalView(APIView):
    def get(self, request, format=None):
        try:
            cart = Carrito.objects.get(user=request.user)
            cart_items = CarritoItem.objects.filter(carrito=cart)

            # Dinero en entero CLP: precio x cantidad, sumado como entero.
            total_cost = 0
            total_compare_cost = 0
            for cart_item in cart_items:
                total_cost += int(cart_item.product.price) * cart_item.count
                total_compare_cost += int(cart_item.product.compare_price) * cart_item.count

            return Response(
                {'total_cost': total_cost, 'total_compare_cost': total_compare_cost},
                status=status.HTTP_200_OK)
        except Carrito.DoesNotExist:
            return Response(
                {'error': 'Something went wrong when retrieving total costs'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetItemTotalView(APIView):
    def get(self, request, format=None):
        try:
            cart = Carrito.objects.get(user=request.user)
            return Response({'total_items': cart.total_items}, status=status.HTTP_200_OK)
        except Carrito.DoesNotExist:
            return Response(
                {'error': 'Something went wrong when getting total number of items'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateItemView(APIView):
    def put(self, request, format=None):
        data = request.data
        try:
            product_id = int(data['product_id'])
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Product ID must be an integer'},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            count = int(data['count'])
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Count value must be an integer'},
                            status=status.HTTP_404_NOT_FOUND)

        if count < 1:
            return Response({'error': 'La cantidad debe ser al menos 1'},
                            status=status.HTTP_400_BAD_REQUEST)

        cart = Carrito.objects.get(user=request.user)
        item = CarritoItem.objects.filter(carrito=cart, product_id=product_id).first()
        if item is None:
            return Response({'error': 'This product is not in your cart'},
                            status=status.HTTP_404_NOT_FOUND)

        if not _has_available_stock(item.product, count):
            return Response({'error': 'Not enough of this item in stock'},
                            status=status.HTTP_200_OK)

        item.count = count
        item.save(update_fields=['count'])
        _sync_total_items(cart)
        return Response({'cart': _serialize_cart(cart)}, status=status.HTTP_200_OK)


class RemoveItemView(APIView):
    def delete(self, request, format=None):
        data = request.data
        try:
            product_id = int(data['product_id'])
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Product ID must be an integer'},
                            status=status.HTTP_404_NOT_FOUND)

        cart = Carrito.objects.get(user=request.user)
        item = CarritoItem.objects.filter(carrito=cart, product_id=product_id).first()
        if item is None:
            return Response({'error': 'This product is not in your cart'},
                            status=status.HTTP_404_NOT_FOUND)

        item.delete()
        _sync_total_items(cart)
        return Response({'cart': _serialize_cart(cart)}, status=status.HTTP_200_OK)


class EmptyCartView(APIView):
    def delete(self, request, format=None):
        try:
            cart = Carrito.objects.get(user=request.user)
        except Carrito.DoesNotExist:
            return Response({'error': 'Something went wrong emptying cart'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not CarritoItem.objects.filter(carrito=cart).exists():
            return Response({'success': 'Cart is already empty'},
                            status=status.HTTP_200_OK)

        CarritoItem.objects.filter(carrito=cart).delete()
        Carrito.objects.filter(id=cart.id).update(total_items=0)
        return Response({'success': 'Cart emptied successfully'},
                        status=status.HTTP_200_OK)


class SynchCartProduct(APIView):
    """Devuelve los productos (con cantidad) de un carrito anónimo guardado en
    localStorage, para hidratarlo con datos frescos del backend."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        try:
            cart_items = request.data['cart_items']
            result = []
            for entry in cart_items:
                try:
                    count = int(entry.get('count', 1))
                except (TypeError, ValueError):
                    count = 1
                product = Product.objects.get(id=entry['product_id'])
                result.append({
                    'count': max(count, 1),
                    'product': ProductSerializer(product).data,
                })
            return Response({'cart': result}, status=status.HTTP_200_OK)
        except (KeyError, Product.DoesNotExist):
            return Response(
                {'error': 'Ha ocurrido un error mientras intentabamos sincronizar '
                          'su carrito, intente mas tarde'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

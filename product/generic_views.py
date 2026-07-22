from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from category.models import Category
from .models import Attribute, Product
from .serializers import AttributeSerializer, ProductSerializer


SORT_FIELDS = {'date_created', 'price', 'name'}


def _base_products():
    return Product.objects.filter(
        sold=False,
        status=Product.ProductStatus.PUBLISHED,
    ).select_related('category').prefetch_related(
        'attribute_values__attribute_value__attribute',
        'variants__attributes__attribute',
        'galleryproduct_set',
    )


def _category_filter(queryset, category_id):
    if not category_id:
        return queryset
    try:
        category_id = int(category_id)
    except (TypeError, ValueError):
        return None
    if category_id == 0:
        return queryset
    category = get_object_or_404(Category, id=category_id)
    if category.parent:
        return queryset.filter(category=category)
    children = Category.objects.filter(parent=category)
    category_ids = [category.id, *children.values_list('id', flat=True)]
    return queryset.filter(category_id__in=category_ids)


def _apply_filters(queryset, params):
    product_type = params.get('product_type')
    if product_type:
        queryset = queryset.filter(product_type=slugify(product_type))

    search = params.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search),
        )

    min_price = params.get('min_price')
    if min_price not in (None, ''):
        queryset = queryset.filter(price__gte=int(min_price))

    max_price = params.get('max_price')
    if max_price not in (None, ''):
        queryset = queryset.filter(price__lte=int(max_price))

    queryset = _category_filter(queryset, params.get('category_id'))
    if queryset is None:
        return None

    sort_by = params.get('sortBy') or params.get('sort_by') or 'date_created'
    if sort_by not in SORT_FIELDS:
        sort_by = 'date_created'
    if params.get('order') == 'desc':
        sort_by = f'-{sort_by}'
    return queryset.order_by(sort_by)


def _limit(queryset, raw_limit):
    if raw_limit in (None, ''):
        return queryset
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return None
    if limit <= 0:
        return queryset
    return queryset[:limit]


def _get_product(identifier):
    queryset = _base_products()
    try:
        return get_object_or_404(queryset, id=int(identifier))
    except (TypeError, ValueError):
        return get_object_or_404(queryset, slug=identifier)


class ProductListView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        try:
            products = _apply_filters(_base_products(), request.query_params)
            if products is None:
                return Response({'error': 'category_id debe ser un entero'},
                                status=status.HTTP_400_BAD_REQUEST)
            products = _limit(products, request.query_params.get('limit'))
            if products is None:
                return Response({'error': 'limit debe ser un entero'},
                                status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'min_price y max_price deben ser enteros CLP'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'products': ProductSerializer(products, many=True).data},
                        status=status.HTTP_200_OK)


class ProductSearchView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        try:
            products = _apply_filters(_base_products(), request.data)
            if products is None:
                return Response({'error': 'category_id debe ser un entero'},
                                status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'min_price y max_price deben ser enteros CLP'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'search_products': ProductSerializer(products, many=True).data},
                        status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, product_identifier, format=None):
        product = _get_product(product_identifier)
        return Response({'product': ProductSerializer(product).data},
                        status=status.HTTP_200_OK)


class ProductRelatedView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, product_identifier, format=None):
        product = _get_product(product_identifier)
        related = _base_products().filter(
            category=product.category,
            product_type=product.product_type,
        ).exclude(id=product.id).order_by('-date_created')[:3]
        return Response({'related_products': ProductSerializer(related, many=True).data},
                        status=status.HTTP_200_OK)


class AttributeListView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        attributes = Attribute.objects.prefetch_related('values')
        return Response({'attributes': AttributeSerializer(attributes, many=True).data},
                        status=status.HTTP_200_OK)

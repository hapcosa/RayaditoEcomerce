from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .serializers import CategorySerializer
from .models import Category


def _build_category_tree(product_type):
    """Categorías raíz del tipo dado, cada una con sus sub_categories.

    Devuelve una lista (vacía si no hay categorías): una lista vacía es un
    resultado válido, no un error de servidor.
    """
    categories = list(Category.objects.filter(ProductType=product_type))
    result = []
    for category in categories:
        if category.parent:
            continue
        item = {'id': category.id, 'name': category.name, 'sub_categories': []}
        for cat in categories:
            if cat.parent_id == category.id:
                item['sub_categories'].append(
                    {'id': cat.id, 'name': cat.name, 'sub_categories': []})
        result.append(item)
    return result


class ListCategoriesJoyasView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        return Response({'categories': _build_category_tree('Joya')},
                        status=status.HTTP_200_OK)


class ListCategoriesPiedrasView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        return Response({'categories': _build_category_tree('Piedra')},
                        status=status.HTTP_200_OK)


class GetCategoryView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, categoryId, format=None):
        try:
            category_id = int(categoryId)
        except (TypeError, ValueError):
            return Response(
                {'error': 'Error de tipo de dato, no se pudo acceder a la categoria'},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({'error': 'Categoría no encontrada'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({'category': CategorySerializer(category).data},
                        status=status.HTTP_200_OK)

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from  .models import Product, GalleryProduct
from .serializers import GalleryProductSerializer, ProductSerializer
from category.models import Category
from metaproduct.models import *
from django.db.models import Q
# Create your views here.
#piedras api views
class ListAllSearchView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, format=None):
        data = self.request.data

        try:
            category_id = int(data['category_id'])
        except:
            return Response(
                {'error': 'Category ID must be an integer'},
                status=status.HTTP_404_NOT_FOUND)

        search = data['search']

        # Chequear si algo input ocurrio en la busqueda
        if len(search) == 0:
            # mostrar todos los productos si no hay input en la busqueda
            search_results = Product.objects.order_by('-date_created').filter(sold=False)
            
        else:
            # Si hay criterio de busqueda, filtramos con dicho criterio usando Q
            results = Product.objects.filter(
                Q(description__icontains=search) | Q(name__icontains=search)
                )
            search_results=results.filter(sold=False)

        if category_id == 0:
            search_results = ProductSerializer(search_results, many=True)
            return Response(
                {'search_products': search_results.data},
                status=status.HTTP_200_OK)
        

        # revisar si existe categoria
        if not Category.objects.filter(id=category_id).exists():
            return Response(
                {'error': 'Ingreso una categoria invalida'},
                status=status.HTTP_404_NOT_FOUND)

        category = Category.objects.get(id=category_id)

        # si la categoria tiene apdre, fitlrar solo por la categoria y no el padre tambien
        if category.parent:
            search_results = search_results.order_by(
                '-date_created'
            ).filter(category=category)
        
        else:
            # si esta categoria padre no tiene hijjos, filtrar solo la categoria
            if not Category.objects.filter(parent=category).exists():
                search_results = search_results.order_by(
                    '-date_created'
                ).filter(category=category)
        
            else:
                categories = Category.objects.filter(parent=category)
                filtered_categories = [category]

                for cat in categories:
                    filtered_categories.append(cat)
                
                filtered_categories = tuple(filtered_categories)

                search_results = search_results.order_by(
                    '-date_created'
                ).filter(category__in=filtered_categories)
        
        search_results = ProductSerializer(search_results, many=True)
        return Response({'search_products': search_results.data}, status=status.HTTP_200_OK)
class ListGalleryView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request, productId, format = None):
        try:
            product_id = int(productId)
        except:
            return Response(
                {'error': 'Product ID debe ser un numero entero'},
                status=status.HTTP_400_NOT_FOUND
            )
        if GalleryProduct.objects.filter(product=product_id).exists():
            galleryProduct = GalleryProduct.objects.filter(product=product_id)
            galleryProduct = GalleryProductSerializer(galleryProduct, many=True)
            return Response({'gallery': galleryProduct.data}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'el producto no existe'},
                status=status.HTTP_404_NOT_FOUND)
class ListALlBySearchView(APIView):
    permission_classes=(permissions.AllowAny,)
    def post(self, request, format=None):
        data=self.request.data
        try:
            category_id = int(data['category_id'])
        except:
             return Response(
                {'error': 'La Id debe ser un entero'},
                status=status.HTTP_404_NOT_FOUND)
        price_range = data['price_range']
        print(data['sort_By'])
        sortBy = data['sort_By']
        if not ( sortBy == 'date_created' or sortBy == 'price' or sortBy == 'name'):
            sortBy= 'date_created'
        order = data['order']
        if category_id == 0:
            products_results = Product.objects.filter(sold=False)
        elif not Category.objects.filter(id=category_id).exists():
            return Response(
                {'error': 'La categoria no existe'},
                status=status.HTTP_404_NOT_FOUND)
            
        else:
            category = Category.objects.get(id=category_id)
            if category.parent:
                products_results = Product.objects.filter(sold=False, category=category)
            else:
                if not Category.objects.filter(parent=category).exists():
                    products_results = Product.objects.filter(sold=False, category=category)
                else:
                    categories = Category.objects.filter(parent=category)
                    filtered_categories = [category]
                    for cat in categories:
                        filtered_categories.append(cat)
                    filtered_categories = tuple(filtered_categories)
                    products_results = Product.objects.filter(sold=False, category__in=filtered_categories)
        # filtrar por precio
        if price_range == '0 - 19999':
            products_results = products_results.filter(price__gte=0000)
            products_results = products_results.filter(price__lt=20000)
        elif price_range =='20000 - 39999':
            products_results = products_results.filter(price__gte=20000)
            products_results = products_results.filter(price__lt=40000)
        elif price_range =='40000 - 59999':
            products_results = products_results.filter(price__gte=40000)
            products_results = products_results.filter(price__lt=60000)
        elif price_range =='60000 - 79999':
            products_results = products_results.filter(price__gte=60000)
            products_results = products_results.filter(price__lt=80000)
        elif price_range =='80000 - 99999':
            products_results = products_results.filter(price__gte=80000)
            products_results = products_results.filter(price__lt=100000)
        elif price_range == 'mayor a 100000':
            products_results = products_results.filter(price__gte=100000)
        
        if order == 'desc':
            sortBy = '-' + sortBy
            products_results = products_results.order_by(sortBy)
        elif order == 'asc':
            products_results = products_results.order_by(sortBy)
        else:
            products_results = products_results.order_by(sortBy)
            
        products_results = ProductSerializer(products_results, many=True)
        if len(products_results.data) > 0:
            return Response({'filtered_products': products_results.data}, status=status.HTTP_200_OK)
        else:
              return Response(
                {'error': 'los productos no existen'},
                status=status.HTTP_404_NOT_FOUND)                
              
class SaveJoyaView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        data = self.request.data
        if(data['joya'] is not None):
            joya=joyas.objects.create()
            joya.name=data['joya'].name
            joya.type=data['joya'].type
            joya.price=data['joya'].value
            joya.description=data['joya'].description
            joya.photo=data['joya'].photo
            for photo in data['photos']:
                galery.joya=joya.id
                galery=GalleryProduct.objects.create()
                galery.photo=photo
        else:
            return Response(
                {'error': 'debe ingresar datos'},
                status=status.HTTP_404_NOT_FOUND)
        
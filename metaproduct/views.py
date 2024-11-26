from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from .serializers import *
from .models import Material
# Create your views here.
class GetMaterialView(APIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request, MaterialId, format = None):
        try:
            material_id = int(MaterialId)
            print(material_id)
        except:
             return Response(
                {'error': 'Product ID debe ser un numero entero'},
                status=status.HTTP_400_NOT_FOUND)
      
        print("error")
        Material = Material.objects.get(id=product_id)
        print(Material)
        Material = MaterialSerializer(Material)
        return Response({'Material': Material.data}, status=status.HTTP_200_OK)
 
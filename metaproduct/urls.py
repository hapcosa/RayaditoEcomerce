from .views import *
from django.urls import path
app_name = 'metaproduct'

urlpatterns = [
    path('get-material/<MaterialId>', GetMaterialView.as_view()),
]

from django.urls import path
from .views import *
app_name = 'product'

urlpatterns = [
    path('search',  ListAllSearchView.as_view()),
    path('galeryproduct/<productId>', ListGalleryView.as_view()),
    path('by/allsearch', ListALlBySearchView.as_view()),
    path('save-Joya', SaveJoyaView.as_view()),
]

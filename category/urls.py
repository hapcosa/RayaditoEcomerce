from django.urls import path
from .views import *

urlpatterns = [
    path('catalog/<slug:path>', ListCatalogCategoriesView.as_view()),
    path('categories', ListCategoriesJoyasView.as_view()),
    path('piedrascategory', ListCategoriesPiedrasView.as_view()), 
    path('get-category/<categoryId>',GetCategoryView.as_view()),
]

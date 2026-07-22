from django.urls import path

from .generic_views import (
    ProductDetailView,
    ProductListView,
    ProductRelatedView,
    ProductSearchView,
)

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view()),
    path('search', ProductSearchView.as_view()),
    path('related/<str:product_identifier>', ProductRelatedView.as_view()),
    path('<str:product_identifier>', ProductDetailView.as_view()),
]

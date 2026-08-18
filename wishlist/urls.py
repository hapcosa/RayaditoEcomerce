from django.urls import path

from .views import AddWishlistView, ListWishlistView, RemoveWishlistView

app_name = 'wishlist'

urlpatterns = [
    path('list', ListWishlistView.as_view()),
    path('add', AddWishlistView.as_view()),
    path('remove/<int:product_id>', RemoveWishlistView.as_view()),
]

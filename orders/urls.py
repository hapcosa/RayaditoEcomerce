from django.urls import path
from .views import DispatchOrderView, ListOrdersView, ListOrderDetailView

app_name="orders"

urlpatterns = [
    path('get-orders', ListOrdersView.as_view()),
    path('get-order/<transactionId>', ListOrderDetailView.as_view()),
    path('dispatch/<int:order_id>', DispatchOrderView.as_view()),
]

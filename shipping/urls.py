from django.urls import path
from .views import GetShippingView, GetShippingOptionId, QuoteShippingView

urlpatterns = [
    path('get-shipping-options', GetShippingView.as_view()),
    path('get-shipping-option/<ShippingId>', GetShippingOptionId.as_view()),
    path('quote', QuoteShippingView.as_view()),
]

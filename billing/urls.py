from django.urls import path

from .views import BillingConfigView

app_name = 'billing'

urlpatterns = [
    path('config', BillingConfigView.as_view()),
]

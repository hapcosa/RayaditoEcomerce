from django.urls import path

from .generic_views import AttributeListView

app_name = 'attributes'

urlpatterns = [
    path('', AttributeListView.as_view()),
]

from django.urls import path

from .views import HeroImageListView

app_name = 'homepage'

urlpatterns = [
    path('hero', HeroImageListView.as_view()),
]

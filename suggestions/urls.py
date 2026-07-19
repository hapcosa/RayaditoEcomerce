from django.urls import path

from .views import CreateSuggestionView, ListSuggestionsView

app_name = 'suggestions'

urlpatterns = [
    path('create', CreateSuggestionView.as_view()),
    path('list', ListSuggestionsView.as_view()),
]

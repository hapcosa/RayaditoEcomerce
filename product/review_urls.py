from django.urls import path
from .review_views import (
    GetReviewsView,
    GetReviewView,
    CreateReviewView,
    UpdateReviewView,
    DeleteReviewView,
    FilterReviewsView,
)

app_name = 'reviews'

urlpatterns = [
    path('get-reviews/<int:product_id>', GetReviewsView.as_view()),
    path('get-review/<int:product_id>', GetReviewView.as_view()),
    path('create-review/<int:product_id>', CreateReviewView.as_view()),
    path('update-review/<int:product_id>', UpdateReviewView.as_view()),
    path('delete-review/<int:product_id>', DeleteReviewView.as_view()),
    path('filter-reviews/<int:product_id>', FilterReviewsView.as_view()),
]

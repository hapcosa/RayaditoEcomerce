"""API de reseñas (estrellas). Rutas montadas en /api/reviews/ (ver review_urls.py).

El frontend usa medias estrellas: el rating es un múltiplo de 0.5 entre 0.5 y 5.0.
"""
from decimal import Decimal, InvalidOperation

from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product, Review
from .serializers import ReviewSerializer


def _approved_reviews(product):
    return Review.objects.filter(product=product, approved=True)


def _validate_rating(raw):
    """Devuelve un Decimal válido (múltiplo de 0.5 en [0.5, 5.0]) o None."""
    try:
        rating = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if rating < Decimal('0.5') or rating > Decimal('5.0'):
        return None
    if (rating * 2) % 1 != 0:
        return None
    return rating


class GetReviewsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        reviews = _approved_reviews(product)
        return Response({
            'reviews': ReviewSerializer(reviews, many=True).data,
            'count': reviews.count(),
            'average': reviews.aggregate(avg=Avg('rating'))['avg'],
        }, status=status.HTTP_200_OK)


class GetReviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        review = Review.objects.filter(product=product, user=request.user).first()
        data = ReviewSerializer(review).data if review else None
        return Response({'review': data}, status=status.HTTP_200_OK)


class CreateReviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        rating = _validate_rating(request.data.get('rating'))
        if rating is None:
            return Response({'error': 'rating debe ser un múltiplo de 0.5 entre 0.5 y 5.0'},
                            status=status.HTTP_400_BAD_REQUEST)
        if Review.objects.filter(product=product, user=request.user).exists():
            return Response({'error': 'ya tienes una reseña para este producto'},
                            status=status.HTTP_409_CONFLICT)

        # verified_purchase: ¿el usuario compró este producto?
        from orders.models import OrderItem
        verified = OrderItem.objects.filter(
            order__user=request.user, product=product).exists()

        review = Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=(request.data.get('comment') or '').strip(),
            verified_purchase=verified,
        )
        reviews = _approved_reviews(product)
        return Response({
            'review': ReviewSerializer(review).data,
            'reviews': ReviewSerializer(reviews, many=True).data,
        }, status=status.HTTP_201_CREATED)


class UpdateReviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        review = Review.objects.filter(product=product, user=request.user).first()
        if not review:
            return Response({'error': 'no existe reseña para actualizar'},
                            status=status.HTTP_404_NOT_FOUND)
        rating = _validate_rating(request.data.get('rating'))
        if rating is None:
            return Response({'error': 'rating debe ser un múltiplo de 0.5 entre 0.5 y 5.0'},
                            status=status.HTTP_400_BAD_REQUEST)
        review.rating = rating
        review.comment = (request.data.get('comment') or '').strip()
        review.save(update_fields=['rating', 'comment', 'updated_at'])
        reviews = _approved_reviews(product)
        return Response({
            'review': ReviewSerializer(review).data,
            'reviews': ReviewSerializer(reviews, many=True).data,
        }, status=status.HTTP_200_OK)


class DeleteReviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        review = Review.objects.filter(product=product, user=request.user).first()
        if not review:
            return Response({'error': 'no existe reseña para eliminar'},
                            status=status.HTTP_404_NOT_FOUND)
        review.delete()
        reviews = _approved_reviews(product)
        return Response({'reviews': ReviewSerializer(reviews, many=True).data},
                        status=status.HTTP_200_OK)


class FilterReviewsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        reviews = _approved_reviews(product)
        rating = _validate_rating(request.query_params.get('rating'))
        if rating is not None:
            reviews = reviews.filter(rating=rating)
        return Response({'reviews': ReviewSerializer(reviews, many=True).data},
                        status=status.HTTP_200_OK)

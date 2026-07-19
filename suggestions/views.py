"""API del buzón de sugerencias. Rutas montadas en /api/suggestions/.

- create: envío público (anónimo permitido); enlaza el usuario si va autenticado.
- list:   solo staff, para moderar (y alimentar la futura app admin).
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Suggestion
from .serializers import SuggestionCreateSerializer, SuggestionSerializer


class CreateSuggestionView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = SuggestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        suggestion = serializer.save(user=user)
        return Response(
            {
                'suggestion': SuggestionSerializer(suggestion).data,
                'message': '¡Gracias! Recibimos tu mensaje.',
            },
            status=status.HTTP_201_CREATED,
        )


class ListSuggestionsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        suggestions = Suggestion.objects.all()
        kind = request.query_params.get('kind')
        state = request.query_params.get('status')
        if kind:
            suggestions = suggestions.filter(kind=kind)
        if state:
            suggestions = suggestions.filter(status=state)
        return Response(
            {
                'suggestions': SuggestionSerializer(suggestions, many=True).data,
                'count': suggestions.count(),
            },
            status=status.HTTP_200_OK,
        )

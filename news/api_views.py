"""
API views for the News application.

This module defines RESTful API endpoints that allow authenticated
readers to retrieve articles based on their subscriptions.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Article
from .serializers import ArticleSerializer


class SubscribedArticlesAPIView(APIView):
    """
    API endpoint for retrieving subscribed articles.

    Returns approved articles published by publishers or journalists
    that the authenticated reader is subscribed to.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve approved articles for the authenticated reader.

        Only articles associated with the reader's subscriptions are
        returned. Non-reader roles receive an empty response.
        """
 
       user = request.user

        if user.role != "reader":
            return Response([])

        articles = (
            Article.objects.filter(
                approved=True,
                publisher__in=user.subscribed_publishers.all(),
            )
            | Article.objects.filter(
                approved=True,
                journalist__in=user.subscribed_journalists.all(),
            )
        )

        serializer = ArticleSerializer(articles.distinct(), many=True)
        return Response(serializer.data)


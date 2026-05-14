from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter
from .serializers import ArticleSerializer, NewsletterSerializer


class ArticleListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        articles = Article.objects.filter(approved=True).order_by("-created_at")
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != "journalist":
            return Response(
                {"error": "Only journalists can create articles."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArticleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id, approved=True)
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    def put(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.role == "journalist" and article.author != request.user:
            return Response(
                {"error": "You can only edit your own articles."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.role == "journalist" and article.author != request.user:
            return Response(
                {"error": "You can only delete your own articles."},
                status=status.HTTP_403_FORBIDDEN,
            )
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribedArticlesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
                author__in=user.subscribed_journalists.all(),
            )
        ).distinct().order_by("-created_at")
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)


class ApprovedArticleLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {"status": "logged", "data": request.data},
            status=status.HTTP_201_CREATED,
        )


class NewsletterListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        newsletters = Newsletter.objects.all().order_by("-created_at")
        serializer = NewsletterSerializer(newsletters, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = NewsletterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewsletterDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, newsletter_id):
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
        serializer = NewsletterSerializer(newsletter)
        return Response(serializer.data)

    def put(self, request, newsletter_id):
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = NewsletterSerializer(newsletter, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, newsletter_id):
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
        if request.user.role not in ("journalist", "editor"):
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        newsletter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

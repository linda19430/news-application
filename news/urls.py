from django.urls import path
from .views import approve_article
from .api_views import SubscribedArticlesAPIView

urlpatterns = [
    path("approve/<int:article_id>/", approve_article, name="approve_article"),
    path("api/articles/", SubscribedArticlesAPIView.as_view(), name="api_articles"),
]


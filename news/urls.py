from django.urls import path

from .api_views import (
    ApprovedArticleLogAPIView,
    ArticleDetailAPIView,
    ArticleListAPIView,
    NewsletterDetailAPIView,
    NewsletterListAPIView,
    SubscribedArticlesAPIView,
)
from .views import (
    approve_article,
    article_create,
    article_delete,
    article_edit,
    editor_dashboard,
    home,
    journalist_dashboard,
    newsletter_create,
    newsletter_delete,
    newsletter_edit,
    reader_dashboard,
    register,
    reject_article,
    subscribe_journalist,
    subscribe_publisher,
    unsubscribe_journalist,
    unsubscribe_publisher,
    user_login,
    user_logout,
)

urlpatterns = [
    # Auth
    path("", home, name="home"),
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    # Reader
    path("reader/", reader_dashboard, name="reader_dashboard"),
    path(
        "reader/subscribe/publisher/<int:publisher_id>/",
        subscribe_publisher,
        name="subscribe_publisher",
    ),
    path(
        "reader/unsubscribe/publisher/<int:publisher_id>/",
        unsubscribe_publisher,
        name="unsubscribe_publisher",
    ),
    path(
        "reader/subscribe/journalist/<int:journalist_id>/",
        subscribe_journalist,
        name="subscribe_journalist",
    ),
    path(
        "reader/unsubscribe/journalist/<int:journalist_id>/",
        unsubscribe_journalist,
        name="unsubscribe_journalist",
    ),
    # Journalist
    path("journalist/", journalist_dashboard, name="journalist_dashboard"),
    path(
        "journalist/article/create/",
        article_create,
        name="article_create",
    ),
    path(
        "journalist/article/<int:article_id>/edit/",
        article_edit,
        name="article_edit",
    ),
    path(
        "journalist/article/<int:article_id>/delete/",
        article_delete,
        name="article_delete",
    ),
    # Editor
    path("editor/", editor_dashboard, name="editor_dashboard"),
    path(
        "editor/approve/<int:article_id>/",
        approve_article,
        name="approve_article",
    ),
    path(
        "editor/reject/<int:article_id>/",
        reject_article,
        name="reject_article",
    ),
    # Newsletters
    path("newsletter/create/", newsletter_create, name="newsletter_create"),
    path(
        "newsletter/<int:newsletter_id>/edit/",
        newsletter_edit,
        name="newsletter_edit",
    ),
    path(
        "newsletter/<int:newsletter_id>/delete/",
        newsletter_delete,
        name="newsletter_delete",
    ),
    # API
    path(
        "api/articles/",
        ArticleListAPIView.as_view(),
        name="api_articles",
    ),
    path(
        "api/articles/subscribed/",
        SubscribedArticlesAPIView.as_view(),
        name="api_subscribed_articles",
    ),
    path(
        "api/articles/<int:article_id>/",
        ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),
    path(
        "api/approved/",
        ApprovedArticleLogAPIView.as_view(),
        name="api_approved",
    ),
    path(
        "api/newsletters/",
        NewsletterListAPIView.as_view(),
        name="api_newsletters",
    ),
    path(
        "api/newsletters/<int:newsletter_id>/",
        NewsletterDetailAPIView.as_view(),
        name="api_newsletter_detail",
    ),
]

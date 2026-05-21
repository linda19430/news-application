from django.contrib import admin

from .models import Article, Newsletter, Publisher, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin configuration for the custom User model."""

    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff")
    search_fields = ("username", "email")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for Publisher model."""

    list_display = ("name",)
    filter_horizontal = ("editors", "journalists")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for Article model."""

    list_display = ("title", "author", "publisher", "approved", "created_at")
    list_filter = ("approved", "publisher", "created_at")
    search_fields = ("title", "content")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter model."""

    list_display = ("title", "author", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "description")
    filter_horizontal = ("articles",)

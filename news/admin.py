"""
Admin configuration for the News application.

This module registers models with the Django admin site
and customizes their admin interface behavior.
"""

from django.contrib import admin
from .models import User, Publisher, Article


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff")
    search_fields = ("username", "email")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "publisher", "approved", "created_at")
    list_filter = ("approved", "publisher")
    search_fields = ("title",)


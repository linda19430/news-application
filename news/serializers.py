"""
Serializers for the News application.

This module defines serializers that convert Django models
into JSON representations for API responses.
"""

from rest_framework import serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Article model.

    Converts Article instances into JSON for API consumption.
    """

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "publisher",
            "journalist",
            "approved",
            "created_at",
        ]


"""
Automated tests for the News application.

This module contains unit tests that verify API behavior,
including subscription-based article retrieval.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import Publisher, Article

User = get_user_model()


class SubscriptionAPITest(TestCase):
    """
    Test cases for subscription-based article retrieval.

    Ensures that readers receive only articles from publishers
    they are subscribed to.
    """

    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="reader1",
            password="readerpass",
            role="reader",
        )

        self.journalist = User.objects.create_user(
            username="journalist1",
            password="journopass",
            role="journalist",
        )

        self.publisher = Publisher.objects.create(name="Daily Tech")
        self.publisher.journalists.add(self.journalist)

        self.article = Article.objects.create(
            title="Approved Article",
            content="Content",
            journalist=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

        self.reader.subscribed_publishers.add(self.publisher)

    def test_reader_sees_subscribed_articles(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


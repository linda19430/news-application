"""
Database models for the News application.

This module defines the core data structures used by the system,
including a custom user model with role-based behavior, publishers,
and articles that require editorial approval before publication.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Each user is assigned a role (reader, journalist, or editor),
    which determines their permissions and behavior within the system.

    Readers can subscribe to publishers and journalists.
    Journalists can publish articles.
    Editors can review and approve articles.
    """

    ROLE_CHOICES = (
        ("reader", "Reader"),
        ("journalist", "Journalist"),
        ("editor", "Editor"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers",
    )

    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="followers",
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Enforce role constraints AFTER save
        if not is_new and self.role == "journalist":
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()


class Publisher(models.Model):
    """
    Represents a news publisher.

    A publisher may have multiple editors and journalists associated
    with it and can have many subscribed readers.
    """

    name = models.CharField(max_length=255)
    editors = models.ManyToManyField(
        User,
        related_name="editor_publishers",
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        User,
        related_name="journalist_publishers",
        limit_choices_to={"role": "journalist"},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Represents a news article written by a journalist.

    Articles must be approved by an editor before they are considered
    published and visible to subscribed readers.
    """

    title = models.CharField(max_length=255)
    content = models.TextField()
    journalist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": "journalist"},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


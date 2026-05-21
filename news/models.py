from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access and subscription support."""

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
        """Save user, clearing subscriptions if role changed away from reader."""
        if self.pk is not None:
            try:
                orig = User.objects.get(pk=self.pk)
                if orig.role == "reader" and self.role != "reader":
                    self.subscribed_publishers.clear()
                    self.subscribed_journalists.clear()
            except User.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Publisher(models.Model):
    """A news publisher with associated editors and journalists."""

    name = models.CharField(max_length=255)
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="editor_publishers",
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name="journalist_publishers",
        limit_choices_to={"role": "journalist"},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """News article written by a journalist; requires editor approval."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": "journalist"},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """Curated collection of articles created by journalists or editors."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters",
        limit_choices_to={"role__in": ["journalist", "editor"]},
    )
    articles = models.ManyToManyField(Article, blank=True, related_name="newsletters")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

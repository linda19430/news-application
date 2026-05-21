import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def notify_on_approval(sender, instance, created, **kwargs):
    """Send email notifications and post to internal API on article approval."""
    if created or not instance.approved:
        return
    _notify_subscribers(instance)
    _post_to_internal_api(instance)


def _notify_subscribers(article):
    """Collect and email subscribers of the article's publisher and author."""
    publisher_emails = set(
        article.publisher.subscribers.filter(role="reader")
        .exclude(email="")
        .values_list("email", flat=True)
    )
    journalist_emails = set(
        article.author.followers.filter(role="reader")
        .exclude(email="")
        .values_list("email", flat=True)
    )
    recipients = publisher_emails | journalist_emails

    if recipients:
        try:
            send_mail(
                subject=f"New Article: {article.title}",
                message=(
                    f"{article.title}\n\n"
                    f"{article.content[:500]}\n\n"
                    "Read more on our site."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(recipients),
                fail_silently=True,
            )
        except Exception:
            logger.exception(
                "Failed to send notification email for article %s", article.pk
            )


def _post_to_internal_api(article):
    """Post approved article data to the internal /api/approved/ endpoint."""
    base_url = getattr(settings, "SITE_BASE_URL", "http://localhost:8000")
    try:
        requests.post(
            f"{base_url}/api/approved/",
            json={
                "id": article.id,
                "title": article.title,
                "publisher": article.publisher_id,
                "author": article.author_id,
                "approved_at": str(article.created_at),
            },
            timeout=5,
        )
    except requests.RequestException:
        logger.exception(
            "Failed to post article %s to internal API", article.pk
        )

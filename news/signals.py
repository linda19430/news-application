import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article


@receiver(post_save, sender=Article)
def notify_on_approval(sender, instance, created, **kwargs):
    if created or not instance.approved:
        return

    _email_subscribers(instance)
    _post_to_internal_api(instance)


def _email_subscribers(article):
    recipients = set()
    for user in article.publisher.subscribers.filter(role="reader"):
        if user.email:
            recipients.add(user.email)
    for user in article.author.followers.filter(role="reader"):
        if user.email:
            recipients.add(user.email)

    if recipients:
        try:
            send_mail(
                subject=f"New Article: {article.title}",
                message=f"{article.title}\n\n{article.content[:500]}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(recipients),
                fail_silently=True,
            )
        except Exception:
            pass


def _post_to_internal_api(article):
    base_url = getattr(settings, "SITE_BASE_URL", "http://localhost:8000")
    try:
        requests.post(
            f"{base_url}/api/approved/",
            json={
                "id": article.id,
                "title": article.title,
                "publisher": article.publisher_id,
                "author": article.author_id,
            },
            timeout=5,
        )
    except Exception:
        pass

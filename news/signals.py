"""
Signal handlers for the News application.

This module contains Django signal logic that triggers notifications
when specific events occur, such as an article being approved.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
import requests

from .models import Article


@receiver(post_save, sender=Article)
def notify_on_approval(sender, instance, created, **kwargs):
    """
    Send notifications when an article is approved.

    This function is triggered after an Article is saved. When an
    article transitions from unapproved to approved, email
    notifications are sent to subscribed readers and the article
    title is posted to X (Twitter).
    """

    # Do nothing when the article is first created
    if created:
        return

    # Do nothing if the article is not approved
    if not instance.approved:
        return

    # Collect subscriber emails safely
    subscribers = set()

    # Subscribers to the publisher
    for user in instance.publisher.subscribers.all():
        if user.email:
            subscribers.add(user.email)

    # Subscribers to the journalist
    for user in instance.journalist.followers.all():
        if user.email:
            subscribers.add(user.email)

    # Send email notifications
    if subscribers:
        print("Sending email notifications to:", subscribers)
        send_mail(
            subject=f"New Article Approved: {instance.title}",
            message=instance.content,
            from_email="news@app.com",
            recipient_list=list(subscribers),
            fail_silently=False,
        )

    # Simulated X (Twitter) API call
    try:
        print("Posting article to X:", instance.title)
        requests.post(
            "https://api.twitter.com/2/tweets",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={"text": instance.title},
            timeout=5,
        )
    except Exception as e:
        print(" post failed:", e)


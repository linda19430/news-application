"""
View logic for the News application.

This module contains Django views that implement application
workflows such as approving articles.
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from .models import Article


@login_required
@permission_required("news.change_article", raise_exception=True)
def approve_article(request, article_id):
    """
    Approve a pending article.

    This view allows an editor to approve an article, marking it as
    published and triggering notification logic.
    """

    article = get_object_or_404(Article, id=article_id)
    article.approved = True
    article.save()
    return redirect("/admin/")


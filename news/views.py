import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ArticleForm,
    NewsletterForm,
    UserLoginForm,
    UserRegisterForm,
)
from .models import Article, Newsletter, Publisher, User


def home(request):
    articles = (
        Article.objects.filter(approved=True)
        .select_related("author", "publisher")
        .order_by("-created_at")[:20]
    )
    return render(request, "news/home.html", {"articles": articles})


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            _assign_group(user, user.role)
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "news/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}.")
            return redirect("home")
    else:
        form = UserLoginForm()
    return render(request, "news/login.html", {"form": form})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def reader_dashboard(request):
    articles = (
        Article.objects.filter(approved=True)
        .select_related("author", "publisher")
        .order_by("-created_at")
    )
    subscribed_articles = Article.objects.none()
    if request.user.role == "reader":
        subscribed_articles = (
            Article.objects.filter(
                approved=True,
                publisher__in=request.user.subscribed_publishers.all(),
            )
            | Article.objects.filter(
                approved=True,
                author__in=request.user.subscribed_journalists.all(),
            )
        ).distinct().order_by("-created_at")

    publishers = Publisher.objects.all()
    journalists = User.objects.filter(role="journalist")

    return render(request, "news/reader_dashboard.html", {
        "articles": articles,
        "subscribed_articles": subscribed_articles,
        "publishers": publishers,
        "journalists": journalists,
    })


@login_required
def subscribe_publisher(request, publisher_id):
    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.subscribed_publishers.add(publisher)
    messages.success(request, f"Subscribed to {publisher.name}.")
    return redirect("reader_dashboard")


@login_required
def unsubscribe_publisher(request, publisher_id):
    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.subscribed_publishers.remove(publisher)
    messages.success(request, f"Unsubscribed from {publisher.name}.")
    return redirect("reader_dashboard")


@login_required
def subscribe_journalist(request, journalist_id):
    journalist = get_object_or_404(User, id=journalist_id, role="journalist")
    request.user.subscribed_journalists.add(journalist)
    messages.success(request, f"Subscribed to {journalist.username}.")
    return redirect("reader_dashboard")


@login_required
def unsubscribe_journalist(request, journalist_id):
    journalist = get_object_or_404(User, id=journalist_id, role="journalist")
    request.user.subscribed_journalists.remove(journalist)
    messages.success(request, f"Unsubscribed from {journalist.username}.")
    return redirect("reader_dashboard")


@login_required
def journalist_dashboard(request):
    if request.user.role != "journalist":
        messages.error(request, "Access denied.")
        return redirect("home")

    articles = Article.objects.filter(author=request.user).order_by("-created_at")
    newsletters = Newsletter.objects.filter(author=request.user).order_by("-created_at")

    return render(request, "news/journalist_dashboard.html", {
        "articles": articles,
        "newsletters": newsletters,
    })


@login_required
def article_create(request):
    if request.user.role != "journalist":
        messages.error(request, "Only journalists can create articles.")
        return redirect("home")

    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, "Article submitted for review.")
            return redirect("journalist_dashboard")
    else:
        form = ArticleForm()
    return render(request, "news/article_form.html", {"form": form})


@login_required
def article_edit(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user.role not in ("journalist", "editor"):
        messages.error(request, "Access denied.")
        return redirect("home")
    if request.user.role == "journalist" and article.author != request.user:
        messages.error(request, "You can only edit your own articles.")
        return redirect("journalist_dashboard")

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated.")
            return redirect("journalist_dashboard")
    else:
        form = ArticleForm(instance=article)
    return render(request, "news/article_form.html", {"form": form})


@login_required
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.user.role not in ("journalist", "editor"):
        messages.error(request, "Access denied.")
        return redirect("home")
    if request.user.role == "journalist" and article.author != request.user:
        messages.error(request, "You can only delete your own articles.")
        return redirect("journalist_dashboard")

    article.delete()
    messages.success(request, "Article deleted.")
    return redirect("journalist_dashboard")


@login_required
def editor_dashboard(request):
    if request.user.role != "editor":
        messages.error(request, "Access denied.")
        return redirect("home")

    pending = Article.objects.filter(approved=False).order_by("-created_at")
    approved = Article.objects.filter(approved=True).order_by("-created_at")
    newsletters = Newsletter.objects.all().order_by("-created_at")

    return render(request, "news/editor_dashboard.html", {
        "pending": pending,
        "approved": approved,
        "newsletters": newsletters,
    })


@login_required
def approve_article(request, article_id):
    if request.user.role != "editor":
        messages.error(request, "Only editors can approve articles.")
        return redirect("home")

    article = get_object_or_404(Article, id=article_id)
    article.approved = True
    article.save(update_fields=["approved"])

    _notify_subscribers(article)
    _post_to_api(article)

    messages.success(request, f'Article "{article.title}" approved.')
    return redirect("editor_dashboard")


@login_required
def reject_article(request, article_id):
    if request.user.role != "editor":
        messages.error(request, "Only editors can reject articles.")
        return redirect("home")

    article = get_object_or_404(Article, id=article_id, approved=False)
    title = article.title
    article.delete()
    messages.warning(request, f'Article "{title}" has been rejected and removed.')
    return redirect("editor_dashboard")


@login_required
def newsletter_create(request):
    if request.user.role not in ("journalist", "editor"):
        messages.error(request, "Access denied.")
        return redirect("home")

    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(request, "Newsletter created.")
            return redirect("home")
    else:
        form = NewsletterForm()
    return render(request, "news/newsletter_form.html", {"form": form})


@login_required
def newsletter_edit(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if request.user.role not in ("journalist", "editor"):
        messages.error(request, "Access denied.")
        return redirect("home")

    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, "Newsletter updated.")
            return redirect("home")
    else:
        form = NewsletterForm(instance=newsletter)
    return render(request, "news/newsletter_form.html", {"form": form})


@login_required
def newsletter_delete(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if request.user.role not in ("journalist", "editor"):
        messages.error(request, "Access denied.")
        return redirect("home")

    newsletter.delete()
    messages.success(request, "Newsletter deleted.")
    return redirect("home")


def _assign_group(user, role):
    group_name = role.capitalize()
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    _set_group_permissions(group, role)


def _set_group_permissions(group, role):
    content_type = ContentType.objects.get_for_model(Article)
    if role == "reader":
        perms = Permission.objects.filter(
            content_type=content_type,
            codename__in=["view_article"],
        )
    elif role == "journalist":
        perms = Permission.objects.filter(
            content_type=content_type,
            codename__in=["add_article", "change_article", "delete_article", "view_article"],
        )
    elif role == "editor":
        perms = Permission.objects.filter(
            content_type=content_type,
            codename__in=["change_article", "delete_article", "view_article"],
        )
    else:
        return
    group.permissions.set(perms)


def _notify_subscribers(article):
    subscribers = set()
    for user in article.publisher.subscribers.filter(role="reader"):
        if user.email:
            subscribers.add(user.email)
    for user in article.author.followers.filter(role="reader"):
        if user.email:
            subscribers.add(user.email)

    if subscribers:
        try:
            send_mail(
                subject=f"New Article: {article.title}",
                message=f"{article.title}\n\n{article.content[:500]}\n\nRead more on our site.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(subscribers),
                fail_silently=True,
            )
        except Exception:
            pass


def _post_to_api(article):
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
    except Exception:
        pass

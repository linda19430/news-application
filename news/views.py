from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ArticleForm,
    NewsletterForm,
    UserLoginForm,
    UserRegisterForm,
)
from .models import Article, Newsletter, Publisher, User


def home(request):
    """Home page showing the 20 most recent approved articles."""
    articles = (
        Article.objects.filter(approved=True)
        .select_related("author", "publisher")
        .order_by("-created_at")[:20]
    )
    return render(request, "news/home.html", {"articles": articles})


def register(request):
    """User registration with automatic group assignment and login."""
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
    """Login view using Django's AuthenticationForm."""
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
    """Logout the current user and redirect to home."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def reader_dashboard(request):
    """Dashboard for readers — browse articles and manage subscriptions."""
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
        ).distinct().select_related("author", "publisher").order_by("-created_at")

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
    """Subscribe the current user to a publisher."""
    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.subscribed_publishers.add(publisher)
    messages.success(request, f"Subscribed to {publisher.name}.")
    return redirect("reader_dashboard")


@login_required
def unsubscribe_publisher(request, publisher_id):
    """Unsubscribe the current user from a publisher."""
    publisher = get_object_or_404(Publisher, id=publisher_id)
    request.user.subscribed_publishers.remove(publisher)
    messages.success(request, f"Unsubscribed from {publisher.name}.")
    return redirect("reader_dashboard")


@login_required
def subscribe_journalist(request, journalist_id):
    """Subscribe the current user to a journalist."""
    journalist = get_object_or_404(User, id=journalist_id, role="journalist")
    request.user.subscribed_journalists.add(journalist)
    messages.success(request, f"Subscribed to {journalist.username}.")
    return redirect("reader_dashboard")


@login_required
def unsubscribe_journalist(request, journalist_id):
    """Unsubscribe the current user from a journalist."""
    journalist = get_object_or_404(User, id=journalist_id, role="journalist")
    request.user.subscribed_journalists.remove(journalist)
    messages.success(request, f"Unsubscribed from {journalist.username}.")
    return redirect("reader_dashboard")


@login_required
def journalist_dashboard(request):
    """Dashboard for journalists — manage own articles and newsletters."""
    if request.user.role != "journalist":
        messages.error(request, "Access denied.")
        return redirect("home")

    articles = (
        Article.objects.filter(author=request.user)
        .select_related("publisher")
        .order_by("-created_at")
    )
    newsletters = (
        Newsletter.objects.filter(author=request.user)
        .prefetch_related("articles")
        .order_by("-created_at")
    )

    return render(request, "news/journalist_dashboard.html", {
        "articles": articles,
        "newsletters": newsletters,
    })


@login_required
def article_create(request):
    """Create a new article (journalists only)."""
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
    """Edit an article — author journalists or any editor."""
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
    """Delete an article — author journalists or any editor."""
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
    """Dashboard for editors — review pending articles and manage content."""
    if request.user.role != "editor":
        messages.error(request, "Access denied.")
        return redirect("home")

    pending = (
        Article.objects.filter(approved=False)
        .select_related("author", "publisher")
        .order_by("-created_at")
    )
    approved = (
        Article.objects.filter(approved=True)
        .select_related("author", "publisher")
        .order_by("-created_at")
    )
    newsletters = (
        Newsletter.objects.all()
        .select_related("author")
        .order_by("-created_at")
    )

    return render(request, "news/editor_dashboard.html", {
        "pending": pending,
        "approved": approved,
        "newsletters": newsletters,
    })


@login_required
def approve_article(request, article_id):
    """Approve an article — the post_save signal handles notifications."""
    if request.user.role != "editor":
        messages.error(request, "Only editors can approve articles.")
        return redirect("home")

    article = get_object_or_404(Article, id=article_id)
    article.approved = True
    article.save(update_fields=["approved"])
    messages.success(request, f'Article "{article.title}" approved.')
    return redirect("editor_dashboard")


@login_required
def reject_article(request, article_id):
    """Reject and delete an unapproved article (editors only)."""
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
    """Create a newsletter (journalists and editors)."""
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
    """Edit a newsletter (journalists and editors)."""
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
    """Delete a newsletter (journalists and editors)."""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if request.user.role not in ("journalist", "editor"):
        messages.error(request, "Access denied.")
        return redirect("home")

    newsletter.delete()
    messages.success(request, "Newsletter deleted.")
    return redirect("home")


def _assign_group(user, role):
    """Assign a user to the appropriate Django group and set permissions."""
    group_name = role.capitalize()
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    _set_group_permissions(group, role)


def _set_group_permissions(group, role):
    """Set object-level Article permissions for the given group."""
    content_type = ContentType.objects.get_for_model(Article)
    codename_map = {
        "reader": ["view_article"],
        "journalist": ["add_article", "change_article", "delete_article", "view_article"],
        "editor": ["change_article", "delete_article", "view_article"],
    }
    codenames = codename_map.get(role, [])
    perms = Permission.objects.filter(
        content_type=content_type,
        codename__in=codenames,
    )
    group.permissions.set(perms)

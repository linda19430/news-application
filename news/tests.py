from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Article, Newsletter, Publisher

User = get_user_model()


class RegistrationTest(TestCase):
    """Tests for user registration with roles and duplicate email validation."""

    def test_register_creates_user_with_role(self):
        response = self.client.post("/register/", {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "role": "reader",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.role, "reader")
        self.assertTrue(user.groups.filter(name="Reader").exists())

    def test_register_journalist_gets_journalist_group(self):
        response = self.client.post("/register/", {
            "username": "journo",
            "email": "journo@test.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "role": "journalist",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="journo")
        self.assertTrue(user.groups.filter(name="Journalist").exists())

    def test_register_editor_gets_editor_group(self):
        response = self.client.post("/register/", {
            "username": "editorx",
            "email": "editorx@test.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "role": "editor",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="editorx")
        self.assertTrue(user.groups.filter(name="Editor").exists())

    def test_register_duplicate_email_fails(self):
        User.objects.create_user(
            username="existing",
            email="dup@test.com",
            password="pass",
            role="reader",
        )
        response = self.client.post("/register/", {
            "username": "newuser",
            "email": "dup@test.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "role": "reader",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")


class ArticleAPITest(TestCase):
    """Tests for article API endpoints and role-based access control."""

    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="reader1", password="readerpass", role="reader",
        )
        self.editor = User.objects.create_user(
            username="editor1", password="editorpass", role="editor",
        )
        self.journalist = User.objects.create_user(
            username="journalist1", password="journopass", role="journalist",
        )
        self.journalist2 = User.objects.create_user(
            username="journalist2", password="journopass2", role="journalist",
        )

        self.publisher = Publisher.objects.create(name="Daily Tech")
        self.publisher.journalists.add(self.journalist)

        self.publisher2 = Publisher.objects.create(name="Other News")
        self.publisher2.journalists.add(self.journalist2)

        self.article1 = Article.objects.create(
            title="Approved Article", content="Content one",
            author=self.journalist, publisher=self.publisher, approved=True,
        )
        self.article2 = Article.objects.create(
            title="Another Approved", content="Content two",
            author=self.journalist2, publisher=self.publisher2, approved=True,
        )
        self.article3 = Article.objects.create(
            title="Pending Article", content="Not approved",
            author=self.journalist, publisher=self.publisher, approved=False,
        )

        self.reader.subscribed_publishers.add(self.publisher)

    def test_get_all_approved_articles(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_get_subscribed_articles(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_reader_excludes_unsubscribed_publisher(self):
        self.reader.subscribed_publishers.clear()
        self.reader.subscribed_journalists.clear()
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_get_single_article(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get(
            f"/api/articles/{self.article1.id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Approved Article")

    def test_get_unapproved_article_returns_404(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get(
            f"/api/articles/{self.article3.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_api_returns_403(self):
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_create_article(self):
        self.client.login(username="journalist1", password="journopass")
        response = self.client.post("/api/articles/", {
            "title": "New Article",
            "content": "Fresh content",
            "publisher": self.publisher.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Article.objects.filter(title="New Article").count(), 1
        )

    def test_reader_cannot_create_article(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.post("/api/articles/", {
            "title": "Should Fail",
            "content": "x",
            "publisher": self.publisher.id,
        })
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_edit_own_article(self):
        self.client.login(username="journalist1", password="journopass")
        response = self.client.put(
            f"/api/articles/{self.article1.id}/",
            {"title": "Updated Title"},
        )
        self.assertEqual(response.status_code, 200)
        self.article1.refresh_from_db()
        self.assertEqual(self.article1.title, "Updated Title")

    def test_journalist_cannot_edit_others_article(self):
        self.client.login(username="journalist1", password="journopass")
        response = self.client.put(
            f"/api/articles/{self.article2.id}/",
            {"title": "Hacked"},
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_delete_article(self):
        self.client.login(username="editor1", password="editorpass")
        response = self.client.delete(
            f"/api/articles/{self.article1.id}/"
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Article.objects.filter(id=self.article1.id).exists()
        )

    def test_reader_cannot_delete_article(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.delete(
            f"/api/articles/{self.article1.id}/"
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_create_article(self):
        self.client.login(username="editor1", password="editorpass")
        response = self.client.post("/api/articles/", {
            "title": "Should Fail",
            "content": "x",
            "publisher": self.publisher.id,
        })
        self.assertEqual(response.status_code, 403)


class NewsletterAPITest(TestCase):
    """Tests for newsletter API endpoints and role-based access control."""

    def setUp(self):
        self.client = APIClient()
        self.reader = User.objects.create_user(
            username="reader1", password="readerpass", role="reader",
        )
        self.journalist = User.objects.create_user(
            username="journalist1", password="journopass", role="journalist",
        )
        self.editor = User.objects.create_user(
            username="editor1", password="editorpass", role="editor",
        )
        self.publisher = Publisher.objects.create(name="Daily Tech")
        self.article = Article.objects.create(
            title="Test Article", content="Content",
            author=self.journalist, publisher=self.publisher, approved=True,
        )

    def test_journalist_can_create_newsletter(self):
        self.client.login(username="journalist1", password="journopass")
        response = self.client.post("/api/newsletters/", {
            "title": "Weekly Digest",
            "description": "Top stories this week",
            "articles": [self.article.id],
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Newsletter.objects.filter(title="Weekly Digest").exists()
        )

    def test_reader_cannot_create_newsletter(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.post("/api/newsletters/", {
            "title": "Should Fail", "description": "x",
        })
        self.assertEqual(response.status_code, 403)

    def test_any_authenticated_user_can_view_newsletters(self):
        self.client.login(username="reader1", password="readerpass")
        response = self.client.get("/api/newsletters/")
        self.assertEqual(response.status_code, 200)

    def test_editor_can_delete_newsletter(self):
        newsletter = Newsletter.objects.create(
            title="Delete Me", description="x", author=self.journalist,
        )
        self.client.login(username="editor1", password="editorpass")
        response = self.client.delete(
            f"/api/newsletters/{newsletter.id}/"
        )
        self.assertEqual(response.status_code, 204)

    def test_reader_cannot_delete_newsletter(self):
        newsletter = Newsletter.objects.create(
            title="Safe", description="x", author=self.journalist,
        )
        self.client.login(username="reader1", password="readerpass")
        response = self.client.delete(
            f"/api/newsletters/{newsletter.id}/"
        )
        self.assertEqual(response.status_code, 403)


class ArticleApprovalTest(TestCase):
    """Tests for article approval/rejection workflow and signal-triggered
    notifications."""

    def setUp(self):
        self.client = APIClient()
        self.editor = User.objects.create_user(
            username="editor1", password="editorpass", role="editor",
        )
        self.journalist = User.objects.create_user(
            username="journalist1", password="journopass", role="journalist",
        )
        self.reader = User.objects.create_user(
            username="reader1",
            password="readerpass",
            role="reader",
            email="reader@test.com",
        )
        self.publisher = Publisher.objects.create(name="Daily Tech")
        self.publisher.journalists.add(self.journalist)
        self.reader.subscribed_publishers.add(self.publisher)

        self.article = Article.objects.create(
            title="Pending Article", content="Review me",
            author=self.journalist, publisher=self.publisher, approved=False,
        )

    def test_editor_can_approve_article(self):
        self.client.login(username="editor1", password="editorpass")
        self.client.get(f"/editor/approve/{self.article.id}/")
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)

    def test_non_editor_cannot_approve_article(self):
        self.client.login(username="journalist1", password="journopass")
        self.client.get(f"/editor/approve/{self.article.id}/")
        self.article.refresh_from_db()
        self.assertFalse(self.article.approved)

    def test_reject_article_deletes_it(self):
        self.client.login(username="editor1", password="editorpass")
        self.client.get(f"/editor/reject/{self.article.id}/")
        self.assertFalse(
            Article.objects.filter(id=self.article.id).exists()
        )

    def test_cannot_reject_approved_article(self):
        self.article.approved = True
        self.article.save()
        self.client.login(username="editor1", password="editorpass")
        response = self.client.get(
            f"/editor/reject/{self.article.id}/"
        )
        self.assertEqual(response.status_code, 404)

    @patch("news.signals.send_mail")
    def test_approval_triggers_email(self, mock_send):
        self.client.login(username="editor1", password="editorpass")
        self.client.get(f"/editor/approve/{self.article.id}/")
        self.assertTrue(mock_send.called)

    @patch("news.signals.requests.post")
    def test_approval_posts_to_api(self, mock_post):
        self.client.login(username="editor1", password="editorpass")
        self.client.get(f"/editor/approve/{self.article.id}/")
        self.assertTrue(mock_post.called)


class SignalTest(TestCase):
    """Tests for the post_save signal that handles article approval
    notifications."""

    def setUp(self):
        self.reader = User.objects.create_user(
            username="reader1",
            password="readerpass",
            role="reader",
            email="reader@test.com",
        )
        self.journalist = User.objects.create_user(
            username="journalist1", password="journopass", role="journalist",
        )
        self.editor = User.objects.create_user(
            username="editor1", password="editorpass", role="editor",
        )
        self.publisher = Publisher.objects.create(name="Daily Tech")
        self.reader.subscribed_publishers.add(self.publisher)
        self.article = Article.objects.create(
            title="Signal Test", content="Testing signals",
            author=self.journalist, publisher=self.publisher, approved=False,
        )

    @patch("news.signals.send_mail")
    @patch("news.signals.requests.post")
    def test_signal_fires_on_approval(self, mock_post, mock_send):
        self.article.approved = True
        self.article.save(update_fields=["approved"])
        self.assertTrue(mock_send.called)
        self.assertTrue(mock_post.called)

    @patch("news.signals.send_mail")
    def test_signal_fires_when_article_approved(self, mock_send):
        self.article.approved = True
        self.article.save()
        self.assertTrue(mock_send.called)

    @patch("news.signals.send_mail")
    @patch("news.signals.requests.post")
    def test_signal_does_not_fire_for_unapproved(self, mock_post, mock_send):
        self.article.title = "Changed"
        self.article.save()
        self.assertFalse(mock_send.called)
        self.assertFalse(mock_post.called)


class SubscriptionTest(TestCase):
    """Tests for reader subscription management."""

    def setUp(self):
        self.client = APIClient()
        self.reader = User.objects.create_user(
            username="reader1", password="readerpass", role="reader",
        )
        self.journalist = User.objects.create_user(
            username="journalist1", password="journopass", role="journalist",
        )
        self.publisher = Publisher.objects.create(name="Daily Tech")

    def test_reader_can_subscribe_to_publisher(self):
        self.client.login(username="reader1", password="readerpass")
        self.client.get(
            f"/reader/subscribe/publisher/{self.publisher.id}/"
        )
        self.assertIn(
            self.publisher, self.reader.subscribed_publishers.all()
        )

    def test_reader_can_subscribe_to_journalist(self):
        self.client.login(username="reader1", password="readerpass")
        self.client.get(
            f"/reader/subscribe/journalist/{self.journalist.id}/"
        )
        self.assertIn(
            self.journalist, self.reader.subscribed_journalists.all()
        )

    def test_reader_can_unsubscribe_from_publisher(self):
        self.reader.subscribed_publishers.add(self.publisher)
        self.client.login(username="reader1", password="readerpass")
        self.client.get(
            f"/reader/unsubscribe/publisher/{self.publisher.id}/"
        )
        self.assertNotIn(
            self.publisher, self.reader.subscribed_publishers.all()
        )


class ApprovedAPITest(TestCase):
    """Tests for the internal approved-article logging endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.journalist = User.objects.create_user(
            username="journalist1", password="journopass", role="journalist",
        )

    def test_approved_endpoint_logs_data(self):
        self.client.login(username="journalist1", password="journopass")
        response = self.client.post("/api/approved/", {
            "id": 1, "title": "Test", "publisher": 1, "author": 1,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "logged")

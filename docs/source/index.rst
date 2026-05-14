News Application Documentation
==============================

A Django-based news application with role-based access control, subscription
management, article approval workflow, and RESTful API.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Models
------

User
~~~~
Custom user model extending Django's AbstractUser. Each user has a role
(reader, journalist, or editor) which determines their permissions.

- ``subscribed_publishers``: ManyToManyField to Publisher
- ``subscribed_journalists``: ManyToManyField to User (self-referential)

Publisher
~~~~~~~~~
Represents a news publisher with associated editors and journalists.

Article
~~~~~~~
News articles written by journalists. Must be approved by an editor before
becoming visible to readers.

- ``title``: CharField (max 255)
- ``content``: TextField
- ``author``: ForeignKey to User (journalists only)
- ``publisher``: ForeignKey to Publisher
- ``approved``: BooleanField (default False)
- ``created_at``: DateTimeField (auto_now_add)

Newsletter
~~~~~~~~~~
Curated collections of articles created by journalists or editors.

- ``title``: CharField (max 255)
- ``description``: TextField
- ``author``: ForeignKey to User
- ``articles``: ManyToManyField to Article

Views
-----

Authentication
~~~~~~~~~~~~~~
- ``register``: User registration with role selection and automatic group assignment
- ``user_login``: Login form using Django's AuthenticationForm
- ``user_logout``: Session logout

Reader
~~~~~~
- ``reader_dashboard``: View articles and manage subscriptions
- ``subscribe_publisher`` / ``unsubscribe_publisher``
- ``subscribe_journalist`` / ``unsubscribe_journalist``

Journalist
~~~~~~~~~~
- ``journalist_dashboard``: View own articles and newsletters
- ``article_create``, ``article_edit``, ``article_delete``

Editor
~~~~~~
- ``editor_dashboard``: Review pending articles, view approved articles
- ``approve_article``: Approve and notify subscribers
- ``reject_article``: Delete unapproved articles

Newsletters
~~~~~~~~~~~
- ``newsletter_create``, ``newsletter_edit``, ``newsletter_delete``

API Endpoints
-------------
All endpoints require authentication (session-based).

- ``GET /api/articles/``: List all approved articles
- ``GET /api/articles/subscribed/``: Reader's subscribed articles
- ``GET /api/articles/<id>/``: Retrieve a single approved article
- ``POST /api/articles/``: Create article (journalists only)
- ``PUT /api/articles/<id>/``: Update article (journalists own, editors)
- ``DELETE /api/articles/<id>/``: Delete article (journalists own, editors)
- ``POST /api/approved/``: Log approved article data
- ``GET /api/newsletters/``: List all newsletters
- ``POST /api/newsletters/``: Create newsletter (journalists, editors)
- ``PUT /api/newsletters/<id>/``: Update newsletter
- ``DELETE /api/newsletters/<id>/``: Delete newsletter

Signals
-------
- ``notify_on_approval``: post_save signal on Article that triggers email
  notifications to subscribers and posts to the internal /api/approved/ endpoint
  when an article is approved.

Tests
-----
35 automated tests covering:
- User registration with roles and duplicate email validation
- API access control per role (reader, journalist, editor)
- Article CRUD operations via API
- Newsletter CRUD operations via API
- Article approval and rejection flows
- Email and API posting via signals (mocked)
- Reader subscription management

News Application Documentation
==============================

A Django-based news application with role-based access control, subscription
management, article approval workflow, and RESTful API.

Setup
-----

Prerequisites
~~~~~~~~~~~~~

- Python 3.8+
- MariaDB 10.3+ (or MySQL 5.7+) — primary
- SQLite (secondary, for local development)
- Docker and Docker Compose (containerized deployment)

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Copy ``.env.example`` to ``.env`` and configure the variables
before running the application.

.. code-block:: bash

   cp .env.example .env

Key variables:

- ``SECRET_KEY`` — Django secret key (generate with ``python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"``)
- ``DB`` — set to ``mysql`` for MariaDB/MySQL, omit for SQLite
- ``DB_PASSWORD`` — database password (required when DB=mysql)

Database — MariaDB (Primary)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install MariaDB and create the database:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt install mariadb-server libmariadb-dev

   # Create database and user
   sudo mysql -u root

.. code-block:: sql

   CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'your-password';
   GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';
   FLUSH PRIVILEGES;

Then set ``DB=mysql`` in your ``.env`` file.

Database — SQLite (Secondary)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use SQLite, simply omit or unset the ``DB`` variable in ``.env``.
No additional setup is required. The application creates ``db.sqlite3``
automatically.

Installation
~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/linda19430/news-application.git
   cd news-application

   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   cp .env.example .env    # edit .env with your values
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver

Access the application at http://localhost:8000

Docker Deployment
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   docker build -t news-app .
   docker run -p 8000:8000 --env-file .env news-app

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
- ``description``: TextField (blank allowed)
- ``author``: ForeignKey to User (journalist or editor)
- ``articles``: ManyToManyField to Article
- ``created_at``: DateTimeField (auto_now_add)

Views
-----

Authentication
~~~~~~~~~~~~~~
- ``register``: User registration with role selection and automatic group assignment
- ``user_login``: Login form using Django's AuthenticationForm
- ``user_logout``: Session logout

Reader
~~~~~~
- ``reader_dashboard``: View approved articles and manage subscriptions
- ``subscribe_publisher`` / ``unsubscribe_publisher``
- ``subscribe_journalist`` / ``unsubscribe_journalist``

Journalist
~~~~~~~~~~
- ``journalist_dashboard``: View own articles and newsletters
- ``article_create``, ``article_edit``, ``article_delete``

Editor
~~~~~~
- ``editor_dashboard``: Review pending articles, view approved articles
- ``approve_article``: Approve article — signals handle email and API notifications
- ``reject_article``: Delete unapproved articles

Newsletters
~~~~~~~~~~~
- ``newsletter_create``, ``newsletter_edit``, ``newsletter_delete``

API Endpoints
-------------
All endpoints require authentication (session-based or basic).

+----------+----------------------------------+----------------------------------+
| Method   | Endpoint                         | Access                           |
+==========+==================================+==================================+
| GET      | /api/articles/                   | All authenticated users          |
+----------+----------------------------------+----------------------------------+
| GET      | /api/articles/subscribed/        | Readers (filtered by subs)       |
+----------+----------------------------------+----------------------------------+
| GET      | /api/articles/<id>/              | All authenticated users          |
+----------+----------------------------------+----------------------------------+
| POST     | /api/articles/                   | Journalists only                 |
+----------+----------------------------------+----------------------------------+
| PUT      | /api/articles/<id>/              | Journalists (own), Editors       |
+----------+----------------------------------+----------------------------------+
| DELETE   | /api/articles/<id>/              | Journalists (own), Editors       |
+----------+----------------------------------+----------------------------------+
| POST     | /api/approved/                   | Internal (logs approved article) |
+----------+----------------------------------+----------------------------------+
| GET      | /api/newsletters/                | All authenticated users          |
+----------+----------------------------------+----------------------------------+
| POST     | /api/newsletters/                | Journalists, Editors             |
+----------+----------------------------------+----------------------------------+
| PUT      | /api/newsletters/<id>/           | Journalists, Editors             |
+----------+----------------------------------+----------------------------------+
| DELETE   | /api/newsletters/<id>/           | Journalists, Editors             |
+----------+----------------------------------+----------------------------------+

Signals
-------
- ``notify_on_approval``: post_save signal on Article that triggers email
  notifications to subscribers and posts to the internal /api/approved/ endpoint
  when an article is approved.

The signal uses ``values_list`` querysets for efficient email collection and
logs any failures via Python's logging framework rather than silently
swallowing exceptions.

User Roles
----------

- **Reader** — View approved articles and newsletters; subscribe/unsubscribe
- **Journalist** — Create, edit, delete own articles and newsletters
- **Editor** — Review, approve, reject articles; manage newsletters

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

Run with:

.. code-block:: bash

   python manage.py test

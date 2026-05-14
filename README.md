# News Application

A Django-based news application that allows readers to view and subscribe to articles from multiple publishers and journalists. Journalists create and manage articles, while editors review and approve content before publication.

## Features

- **Role-based access control** — Reader, Journalist, Editor roles with group permissions
- **Reader subscriptions** — Subscribe to publishers and individual journalists
- **Article approval workflow** — Editors approve articles; email notifications sent to subscribers
- **Newsletter management** — Journalists and editors can curate article collections
- **RESTful API** — Full CRUD for articles and newsletters with role-based authorization
- **Internal API logging** — Approved articles logged to `/api/approved/`
- **Automated tests** — 35 unit tests covering all roles, API endpoints, and signals

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)

## Quick Start — Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Access at http://localhost:8000

## Quick Start — Docker

```bash
docker build -t news-app .
docker run -p 8000:8000 news-app
```

Or with Docker Compose:

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | (change in production) |
| `DB` | Use `mysql` for MySQL/MariaDB | `sqlite` |
| `DB_NAME` | Database name | `news_db` |
| `DB_USER` | Database user | `news_user` |
| `DB_PASSWORD` | Database password | (required for MySQL) |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `SITE_BASE_URL` | Base URL for internal API calls | `http://localhost:8000` |

## User Roles

| Role | Permissions |
|------|-------------|
| **Reader** | View articles/newsletters; subscribe to publishers and journalists |
| **Journalist** | Create, edit, delete own articles and newsletters |
| **Editor** | Review, approve, reject articles; manage newsletters |

## API Endpoints

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/api/articles/` | All authenticated users |
| GET | `/api/articles/subscribed/` | Readers (filtered by subscriptions) |
| GET | `/api/articles/<id>/` | All authenticated users |
| POST | `/api/articles/` | Journalists only |
| PUT | `/api/articles/<id>/` | Journalists (own), Editors |
| DELETE | `/api/articles/<id>/` | Journalists (own), Editors |
| POST | `/api/approved/` | Internal (logs approved articles) |
| GET | `/api/newsletters/` | All authenticated users |
| POST | `/api/newsletters/` | Journalists, Editors |
| PUT | `/api/newsletters/<id>/` | Journalists, Editors |
| DELETE | `/api/newsletters/<id>/` | Journalists, Editors |

## Running Tests

```bash
python manage.py test
```

## Documentation

Sphinx documentation is in `docs/build/html/`. Rebuild with:

```bash
cd docs
make html
```

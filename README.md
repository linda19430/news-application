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
- MariaDB 10.3+ (or MySQL 5.7+)
- Docker and Docker Compose (for containerized deployment)

## Database Setup — MariaDB

This project uses MariaDB as the primary database. SQLite is available as a secondary option for local development.

### Install MariaDB

```bash
# Ubuntu/Debian
sudo apt install mariadb-server libmariadb-dev

# macOS
brew install mariadb

# Start the service
sudo systemctl start mariadb   # Linux
brew services start mariadb    # macOS
```

### Create the database and user

```bash
sudo mysql -u root
```

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Quick Start

### 1. Clone and set up environment

```bash
git clone https://github.com/linda19430/news-application.git
cd news-application

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your values:

- `SECRET_KEY` — generate one with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DB_PASSWORD` — the password you set for the MariaDB user
- Leave `DB=mysql` for MariaDB, or remove it to use SQLite

### 3. Run migrations and start the server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Access the application at http://localhost:8000

## Using SQLite (secondary option)

To use SQLite instead of MariaDB, comment out or remove the `DB=mysql` line in your `.env` file. The application will automatically fall back to SQLite with no additional setup required.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | (required — generate one) |
| `DB` | Set to `mysql` for MariaDB/MySQL | (unset = SQLite) |
| `DB_NAME` | Database name | `news_db` |
| `DB_USER` | Database user | `news_user` |
| `DB_PASSWORD` | Database password | (required when DB=mysql) |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `EMAIL_BACKEND` | Email backend class | `console` |
| `DEFAULT_FROM_EMAIL` | Sender email address | `news@app.com` |
| `SITE_BASE_URL` | Base URL for internal API calls | `http://localhost:8000` |

## Quick Start — Docker

```bash
docker build -t news-app .
docker run -p 8000:8000 --env-file .env news-app
```

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

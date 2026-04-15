# The Speedy Spectator — News Application

A Django-based news portal supporting multiple user roles, article management,
newsletter creation, and a RESTful API with JWT authentication.

---

## Project Overview

The Speedy Spectator is a news application built as part of a Level 2
Introduction to Software Engineering capstone project. It allows journalists
to write and publish articles, editors to review and approve content, and
readers to subscribe to journalists and publishers.

---

## Features

- Role-based access control (Reader, Journalist, Editor)
- Article creation, approval, and publishing workflow
- Newsletter creation and management
- Reader subscriptions to journalists and publishers
- RESTful API with JWT token authentication
- Django Signals for email notifications on article approval
- Internal API endpoint for simulating third-party integration
- Automated unit tests (44 tests)

---

## Tech Stack

- Python 3.12
- Django 5.1
- Django REST Framework
- djangorestframework-simplejwt
- MariaDB / MySQL
- HTML / CSS (custom stylesheet)

---

## System Requirements

Before getting started, make sure the following are installed on your system:

### Python 3.12

Download and install Python 3.12 from https://www.python.org/downloads/

On macOS you can also install it via Homebrew:
```bash
brew install python@3.12
```

On Windows, download the installer from the Python website and ensure
"Add Python to PATH" is checked during installation.

On Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

### MariaDB

Install MariaDB for your operating system:

**macOS (Homebrew):**
```bash
brew install mariadb
brew services start mariadb
```

**Windows:**
Download the installer from https://mariadb.org/download/

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mariadb-server
sudo systemctl start mariadb
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ScottB132/news_project.git
cd news_project
```

### 2. Create a Virtual Environment

**macOS / Linux:**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the provided example file to create your own `.env` file:

```bash
cp .env.example .env
```

Open `.env` and update the values with your own credentials:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=news_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

> **Note:** Never commit your `.env` file to version control.
> The `.env.example` file is provided as a safe template.

### 5. Create the Database

Log in to MariaDB:

```bash
mysql -u root -p
```

Run the following SQL commands to create the database and user:

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON news_db.* TO 'your_db_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

> Replace `your_db_user` and `your_db_password` with the values you set
> in your `.env` file.

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create a Superuser

```bash
python manage.py createsuperuser
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## User Roles

| Role       | Permissions                                               |
|------------|-----------------------------------------------------------|
| Reader     | View approved articles and newsletters, subscribe         |
| Journalist | Create, view, update, delete own articles and newsletters |
| Editor     | View, update, delete all articles and newsletters, approve|

### Creating the First Editor Account

Since editor registration is restricted to existing editors, create the
first editor via the Django admin panel:

1. Log in to `http://127.0.0.1:8000/admin/` with your superuser credentials.
2. Navigate to `newsApp > Users`.
3. Find the user and set their role to `editor`.

---

## REST API

### Authentication

```bash
# Get JWT token
POST /news/api/token/
{"username": "your_username", "password": "your_password"}

# Refresh token
POST /news/api/token/refresh/
{"refresh": "your_refresh_token"}
```

### Endpoints

| Method | Endpoint                          | Role Required        |
|--------|-----------------------------------|----------------------|
| GET    | /news/api/articles/               | Any authenticated    |
| POST   | /news/api/articles/               | Journalist           |
| GET    | /news/api/articles/<id>/          | Any authenticated    |
| PUT    | /news/api/articles/<id>/          | Journalist / Editor  |
| DELETE | /news/api/articles/<id>/          | Journalist / Editor  |
| POST   | /news/api/articles/<id>/approve/  | Editor               |
| GET    | /news/api/articles/subscribed/    | Reader               |
| GET    | /news/api/newsletters/            | Any authenticated    |
| POST   | /news/api/newsletters/            | Journalist / Editor  |
| GET    | /news/api/newsletters/<id>/       | Any authenticated    |
| PUT    | /news/api/newsletters/<id>/       | Journalist / Editor  |
| DELETE | /news/api/newsletters/<id>/       | Journalist / Editor  |
| GET    | /news/api/users/me/               | Any authenticated    |
| POST   | /news/api/approved/               | Internal use         |

### Example API Usage

```bash
# Save token to a variable (macOS / Linux)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/news/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}' \
     | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

# Get all articles
curl -X GET http://127.0.0.1:8000/news/api/articles/ \
     -H "Authorization: Bearer $TOKEN"

# Create an article (journalist only)
curl -X POST http://127.0.0.1:8000/news/api/articles/ \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title": "My Article", "content": "Article content."}'

# Approve an article (editor only)
curl -X POST http://127.0.0.1:8000/news/api/articles/1/approve/ \
     -H "Authorization: Bearer $TOKEN"
```

---

## Django Signals

When an article is approved by an editor:

1. **Email notification** — sent to all readers subscribed to the article's
   journalist or publisher (prints to console in development).
2. **Internal API call** — a POST request is made to `/news/api/approved/`
   simulating a third-party integration.

---

## Running Tests

```bash
python manage.py test newsApp
```

---

## Troubleshooting

### Access denied for database user

Ensure the credentials in your `.env` file match the MariaDB user you created
in Step 5. If you're on macOS and getting socket errors, set `DB_HOST=127.0.0.1`
instead of `localhost`.

### `load_dotenv` not loading variables

Ensure your `.env` file is in the same directory as `manage.py` (the project
root). The settings file loads it using the absolute path:
`load_dotenv(BASE_DIR / ".env")`.

### `python3` not found on Windows

Use `python` instead of `python3` on Windows. All commands in this README
that use `python3` should be run as `python` on Windows.

---

## Author

Created by Scott Bedford as part of a software engineering capstone project.

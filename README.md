# Speedy Spectator News Application

A Django-based news platform supporting readers, journalists, and editors.

---

## Running with venv

### 1. Clone the repository
```bash
git clone https://github.com/ScottB132/news_project.git
cd news_project
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root with the following:

nano .env

SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

The Speedy Spectator — News Application

A Django-based news portal supporting multiple user roles, article management,
newsletter creation, and a RESTful API with JWT authentication.

---

## Project Overview

The Speedy Spectator is a news application built as part of a Level 2
Introduction to Software Engineering capstone project. It allows journalists
to write and publish articles, editors to review and approve content, and
readers to subscribe to journalists and publishers and receive notifications
when new content is approved.

---

## Features

- Role-based access control (Reader, Journalist, Editor)
- Article creation, approval, and publishing workflow
- Newsletter creation and management
- Publisher management — journalists can join publishers, editors can manage them
- Reader subscriptions to journalists and publishers
- Email notifications when articles are approved
- RESTful API with JWT token authentication
- Django Signals for email notifications on article approval
- Internal API endpoint for simulating third-party integration
- Automated unit tests (44 tests)

---

## Tech Stack

- Python 3.12
- Django 4.2.30
- Django REST Framework
- djangorestframework-simplejwt
- MariaDB
- PyMySQL
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
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=news_project
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306

> **Note:** Never commit your `.env` file to version control.
> The `.env.example` file is provided as a safe template.

### 5. Create the Database

Log in to MariaDB:

```bash
mysql -u root -p -h 127.0.0.1 -P 3306
```

Run the following SQL commands to create the database and user:

```sql
CREATE DATABASE news_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON news_project.* TO 'your_db_user'@'localhost';
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

| Role       | Permissions                                                                     |
|------------|---------------------------------------------------------------------------------|
| Reader     | View approved articles and newsletters, subscribe to journalists and publishers |
| Journalist | Create, view, update, delete own articles and newsletters, join/leave publishers|
| Editor     | View, update, delete all articles and newsletters, approve/reject articles,     |
|            | create/manage publishers, register new editors                                  |

### Creating the first Editor account

Since editor registration is restricted to existing editors, create the
first editor via the Django admin panel:

1. Run the server and go to `http://127.0.0.1:8000/admin/`
2. Log in with your superuser credentials
3. Click **Users** and find your user
4. Scroll to the **Role** section and change it to `editor`
5. Click **Save**

Once you have one editor account, new editors can be registered through
the app at the login page when logged in as an editor.

---

## Publishers

Publishers represent news organisations. They are managed as objects
rather than user roles.

### Creating a publisher (Editor only)

1. Log in as an editor
2. Click **Publishers** in the navbar
3. Click **+ Create Publisher**
4. Enter the publisher name and optional website
5. Click **Create Publisher**

### Managing publisher journalists (Editor only)

1. Log in as an editor
2. Click **Publishers** in the navbar
3. Click **View** on a publisher
4. Click **+ Add Journalist** to add a journalist to the publisher
5. Click **Remove** next to a journalist to remove them

### Joining a publisher (Journalist only)

1. Log in as a journalist
2. Click **Publishers** in the navbar
3. Find the publisher you want to join
4. Click **Join**
5. To leave a publisher click **Leave** on the same page

### Subscribing to publishers and journalists (Reader only)

1. Log in as a reader
2. Click **Publishers** in the navbar to browse and subscribe to publishers
3. Click **Journalists** in the navbar to browse and subscribe to journalists
4. Click **Subscribe** to follow a journalist or publisher
5. Click **Unsubscribe** to stop following
6. You will receive email notifications when subscribed content is approved

---

## Reader Subscriptions

Readers can subscribe to both journalists and publishers. When an article
from a subscribed journalist or publisher is approved by an editor, the
reader receives an email notification automatically via Django Signals.

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

Expected output:
Found 44 test(s).
Ran 44 tests in ~13s
OK

---

## Daily Startup

```bash
# Start MariaDB
brew services start mariadb

# Activate virtual environment
source venv/bin/activate

# Start the server
python manage.py runserver
```

## Database Backup

Run this before shutting down to avoid data loss:

```bash
mysqldump -u root -p -h 127.0.0.1 -P 3306 news_project > news_project_backup.sql
```

Restore from backup:

```bash
mysql -u admin -p -h 127.0.0.1 -P 3306 news_project < news_project_backup.sql
```

---

## Project Structure
news_project/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── newsApp/
│   ├── models.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── signals.py
│   ├── forms.py
│   ├── admin.py
│   ├── urls.py
│   ├── tests.py
│   ├── templates/
│   │   └── newsApp/
│   │       ├── base.html
│   │       ├── home.html
│   │       ├── login_register.html
│   │       ├── register_journalist.html
│   │       ├── news_list.html
│   │       ├── article_detail.html
│   │       ├── create_article.html
│   │       ├── edit_article.html
│   │       ├── pending_articles.html
│   │       ├── journalist_dashboard.html
│   │       ├── manage_newsletters.html
│   │       ├── newsletter_list.html
│   │       ├── newsletter_detail.html
│   │       ├── edit_newsletter.html
│   │       ├── publisher_list.html
│   │       ├── publisher_detail.html
│   │       ├── publisher_join_confirm.html
│   │       ├── publisher_add_journalist.html
│   │       ├── create_publisher.html
│   │       ├── journalist_list.html
│   │       ├── subscribe_confirm.html
│   │       └── delete_confirm.html
│   └── static/
│       └── newsApp/
│           ├── css/
│           │   └── base.css
│           └── images/
└── news_project/
├── settings.py
├── urls.py
└── wsgi.py

---

## Testing

python manage.py test newsApp

## Troubleshooting

### Access denied for database user

Ensure the credentials in your `.env` file match the MariaDB user you created.
If you are on macOS and getting socket errors, set `DB_HOST=127.0.0.1`
instead of `localhost`.

### MariaDB not starting

```bash
brew services restart mariadb
```

### Virtual environment not activating

Make sure you are in the project root directory where `manage.py` is located:
```bash
cd news_project
source venv/bin/activate
```

### `python3` not found on Windows

Use `python` instead of `python3` on Windows.

---

## License

This project was created for educational purposes as part of a Level 2
Introduction to Software Engineering capstone project.

## Author

Created by Scott Bedford.

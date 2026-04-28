"""
news_project/settings.py

Django settings for the Speedy Spectator news application.

This file loads sensitive configuration values (secret key, database
credentials) from a .env file using python-dotenv. A .env.example file
is provided in the project root showing which variables are required.

Environment variables required in .env:
    - SECRET_KEY:    Django's secret key for cryptographic signing.
    - DEBUG:         Set to 'True' for development, 'False' for production.
    - DB_NAME:       The MySQL database name.
    - DB_USER:       The MySQL database username.
    - DB_PASSWORD:   The MySQL database password.
    - DB_HOST:       The MySQL host address. Defaults to '127.0.0.1'.
    - DB_PORT:       The MySQL port number. Defaults to '3306'.

For production deployment:
    - Set DEBUG=False in .env
    - Add your domain to ALLOWED_HOSTS
    - Configure a real email backend to replace the console backend
    - Ensure SECRET_KEY is a long random string and kept private

Django documentation: https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
# This must be called before any os.getenv() calls below
load_dotenv()


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------

# Build paths inside the project using BASE_DIR
# BASE_DIR points to the project root (the directory containing manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Security Settings
# ---------------------------------------------------------------------------

# Secret key loaded from .env — never hardcode this value or commit it to git
SECRET_KEY = os.getenv('SECRET_KEY')

# Debug mode loaded from .env — must be False in production
# Defaults to False if the environment variable is not set
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Hosts allowed to serve the application
# Add your domain here when deploying to production
# e.g. ALLOWED_HOSTS = ['speedyspectator.com', 'www.speedyspectator.com']
ALLOWED_HOSTS = []


# ---------------------------------------------------------------------------
# Custom User Model
# ---------------------------------------------------------------------------

# Tell Django to use the custom User model defined in newsApp
# This must be set before running the first migration
AUTH_USER_MODEL = 'newsApp.User'


# ---------------------------------------------------------------------------
# Login and Redirect Settings
# ---------------------------------------------------------------------------

# Redirect to the role-based dashboard after login
LOGIN_REDIRECT_URL = 'dashboard_redirect'

# Use the custom login view instead of Django's default /accounts/login/
LOGIN_URL = 'login_user'


# ---------------------------------------------------------------------------
# Installed Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # newsApp must be first to ensure its AppConfig.ready() runs early
    'newsApp.apps.NewsAppConfig',

    # Django built-in applications
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django REST Framework for the RESTful API
    'rest_framework',

    # Simple JWT for token-based authentication
    'rest_framework_simplejwt',
]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    # Security headers (HSTS, etc.)
    'django.middleware.security.SecurityMiddleware',

    # Session handling
    'django.contrib.sessions.middleware.SessionMiddleware',

    # Common HTTP utilities (trailing slash redirect, etc.)
    'django.middleware.common.CommonMiddleware',

    # CSRF protection for form submissions
    'django.middleware.csrf.CsrfViewMiddleware',

    # Attaches the authenticated user to each request
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Flash messages framework
    'django.contrib.messages.middleware.MessageMiddleware',

    # Clickjacking protection via X-Frame-Options header
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ---------------------------------------------------------------------------
# URL Configuration
# ---------------------------------------------------------------------------

# The root URL configuration module for the project
ROOT_URLCONF = 'news_project.urls'


# ---------------------------------------------------------------------------
# Template Configuration
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        # Use Django's built-in template engine
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # No additional template directories outside of app templates
        'DIRS': [],

        # Automatically find templates in each app's templates/ directory
        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                # Adds debug and sql_queries to the template context
                'django.template.context_processors.debug',

                # Adds the current request object to the template context
                'django.template.context_processors.request',

                # Adds the authenticated user and permissions to context
                'django.contrib.auth.context_processors.auth',

                # Adds flash messages to the template context
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# WSGI Configuration
# ---------------------------------------------------------------------------

# The WSGI application used by Django's built-in server and production servers
WSGI_APPLICATION = 'news_project.wsgi.application'


# ---------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------

# MySQL database — credentials loaded from .env
# Requires PyMySQL installed and configured in newsApp/__init__.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_db',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}


# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------

# Enforce password strength requirements for all user registrations
AUTH_PASSWORD_VALIDATORS = [
    {
        # Rejects passwords too similar to the username or email
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # Rejects passwords shorter than 8 characters (Django default)
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        # Rejects commonly used passwords (e.g. 'password', '12345678')
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # Rejects passwords that are entirely numeric
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------------------------------------------------------------
# Django REST Framework Configuration
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    # Use JWT tokens for API authentication
    # Tokens are obtained via POST /api/token/ and included in the
    # Authorization: Bearer <token> header on subsequent requests
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # Require authentication for all API endpoints by default
    # Individual views can override this with their own permission_classes
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# ---------------------------------------------------------------------------
# Email Configuration
# ---------------------------------------------------------------------------

# Console backend prints emails to the terminal during development
# Replace with a real SMTP backend for production deployment
# e.g. EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SMTP server settings — only used when switching to SMTP backend
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# The from address used in all outgoing notification emails
DEFAULT_FROM_EMAIL = 'noreply@speedyspectator.com'


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

# Default language for the application
LANGUAGE_CODE = 'en-us'

# Store all datetime values in UTC in the database
TIME_ZONE = 'UTC'

# Enable Django's translation framework
USE_I18N = True

# Enable timezone-aware datetimes
USE_TZ = True


# ---------------------------------------------------------------------------
# Static Files
# ---------------------------------------------------------------------------

# URL prefix for serving static files (CSS, JS, images)
STATIC_URL = '/static/'

# Additional directories where Django will look for static files
# outside of each app's static/ directory
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'newsApp', 'static'),
]


# ---------------------------------------------------------------------------
# Default Primary Key
# ---------------------------------------------------------------------------

# Use 64-bit integer primary keys for all models by default
# Overrides Django's default of 32-bit AutoField
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

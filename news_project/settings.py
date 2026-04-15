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


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------

# Build paths inside the project using BASE_DIR
# BASE_DIR points to the project root (the directory containing manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent


# Load environment variables from the .env file in the project root.
# BASE_DIR is used to construct the absolute path so load_dotenv always
# finds the file regardless of the working directory the server is started
# from.
load_dotenv(BASE_DIR / ".env")


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
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


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
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ---------------------------------------------------------------------------
# URL Configuration
# ---------------------------------------------------------------------------

ROOT_URLCONF = 'news_project.urls'


# ---------------------------------------------------------------------------
# Template Configuration
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# WSGI Configuration
# ---------------------------------------------------------------------------

WSGI_APPLICATION = 'news_project.wsgi.application'


# ---------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------

# MySQL / MariaDB — credentials loaded from .env file.
# Copy .env.example to .env and update with your own credentials.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'news_db'),
        'USER': os.getenv('DB_USER', 'admin'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}


# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.NumericPasswordValidator'
        ),
    },
]


# ---------------------------------------------------------------------------
# Django REST Framework Configuration
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# ---------------------------------------------------------------------------
# Email Configuration
# ---------------------------------------------------------------------------

# Console backend prints emails to the terminal during development.
# Replace with a real SMTP backend for production deployment.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'noreply@speedyspectator.com'


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static Files
# ---------------------------------------------------------------------------

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'newsApp', 'static'),
]


# ---------------------------------------------------------------------------
# Default Primary Key
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR.parent))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Logging configuration for debugging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        "django_suap_auth": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "simple_history",
    "django_suap_auth",
    "django_suap_auth.profile",
    "django_suap_auth.erros",
    "home",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTHENTICATION_BACKENDS = [
    "django_suap_auth.profile.backends.SuapProfileAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SUAP_AUTH = {
    "CLIENT_ID": os.environ.get("SUAP_AUTH_CLIENT_ID", ""),
    "CLIENT_SECRET": os.environ.get("SUAP_AUTH_CLIENT_SECRET", ""),
    "REDIRECT_URI": os.environ.get("SUAP_AUTH_REDIRECT_URI", "http://localhost:8000/auth/suap/callback/"),
    "SCOPES": os.environ.get("SUAP_AUTH_SCOPES", "identificacao,email").split(","),
    "DIRECT_REDIRECT": os.environ.get("SUAP_AUTH_DIRECT_REDIRECT", "True") == "True",
}

LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/auth/suap/login/"
LOGOUT_REDIRECT_URL = "/"

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

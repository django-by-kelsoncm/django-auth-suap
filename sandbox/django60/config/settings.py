import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file at the beginning
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

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
    "django_suap_auth",
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
    "home.backends.SandboxSuapAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SUAP_AUTH = {
    "CLIENT_ID": os.environ.get("SUAP_CLIENT_ID", ""),
    "CLIENT_SECRET": os.environ.get("SUAP_CLIENT_SECRET", ""),
    "REDIRECT_URI": os.environ.get("SUAP_REDIRECT_URI", "http://localhost:8000/auth/suap/callback/"),
    "SCOPES": ["identificacao", "email"],
    "DIRECT_REDIRECT": os.environ.get("SUAP_DIRECT_REDIRECT", "True") == "True",
    "BACKEND": "home.backends.SandboxSuapAuthBackend",
    "USER_JSON_FIELD": "suap_data",
    "USER_INFO_ENDPOINTS": [
        # RH / Servidor
        "/api/rh/eu/",
        "/api/rh/meus-dados/",
        {
            "endpoint": "/api/rh/meus-vinculos/",
            "namespace": "meus_vinculos",
            "extract_list": "results",
        },
        {
            "endpoint": "/api/rh/servidores_funcao_ativa/?matricula={identificacao}",
            "namespace": "servidores_funcao_ativa",
            "extract_list": "results",
        },
        {
            "endpoint": "/api/rh/meu-historico-funcional/",
            "namespace": "meu_historico_funcional",
            "extract_list": "results",
        },
        # Ensino / Aluno
        {
            "endpoint": "/api/ensino/meus-dados-aluno/",
            "namespace": "meus_dados_aluno",
        },
        {
            "endpoint": "/api/ensino/requisitos-conclusao/",
            "namespace": "requisitos_conclusao",
        },
        {
            "endpoint": "/api/ensino/periodos/",
            "namespace": "periodos",
            "extract_list": "results",
        },
        {
            "endpoint": "/api/ensino/diarios/{semestre}/",
            "for_each": "periodos",
            "namespace": "diarios",
            "extract_list": "results",
        },
        {
            "endpoint": "/api/ensino/meus-periodos-letivos/",
            "namespace": "meus_periodos_letivos",
            "extract_list": "results",
        },
        {
            "endpoint": "/api/ensino/meu-boletim/{ano_letivo}/{periodo_letivo}/",
            "for_each": "meus_periodos_letivos",
            "namespace": "boletins",
            "extract_list": "results",
        },
    ],
}

LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/auth/suap/login/"
LOGOUT_REDIRECT_URL = "/"

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

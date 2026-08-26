SECRET_KEY = "test-secret-key-not-for-production"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "simple_history",
    "django_suap_auth",
    "django_suap_auth.profile",
    "django_suap_auth.jwt",
    "django_suap_auth.erros",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
SUAP_AUTH = {
    "CLIENT_ID": "test-client-id",
    "CLIENT_SECRET": "test-client-secret",
    "REDIRECT_URI": "http://localhost:8000/auth/suap/callback/",
}
AUTHENTICATION_BACKENDS = ["django_suap_auth.backends.SuapAuthBackend"]
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/login/"
ROOT_URLCONF = "tests.urls"
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
SESSION_ENGINE = "django.contrib.sessions.backends.db"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    }
]
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

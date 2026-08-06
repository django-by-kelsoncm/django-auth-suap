# Instalação

## Requisitos

- Python 3.10+
- Django 5.2+

## Instalar do PyPI

Com `uv` (recomendado):

```bash
uv add django-suap-auth
```

Ou com `pip`:

```bash
pip install django-suap-auth
```

## Adicionar a INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    "django_suap_auth",
]
```

## Configurar URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("auth/suap/", include("django_suap_auth.urls")),
]
```

# django-suap-auth

[![PyPI Version](https://img.shields.io/pypi/v/django-suap-auth)](https://pypi.org/project/django-suap-auth/)
[![Python CI and PyPI Deploy](https://github.com/kelsoncm/django-suap-auth/actions/workflows/publish.yml/badge.svg)](https://github.com/kelsoncm/django-suap-auth/actions/workflows/publish.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-suap-auth.svg)](https://pypi.org/project/django-suap-auth/)
[![Django Versions](https://img.shields.io/badge/django-5.2%20|%206.0-blue)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/kelsoncm/django-suap-auth/actions/workflows/test.yml/badge.svg)](https://github.com/kelsoncm/django-suap-auth/actions/workflows/test.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Coverage](https://codecov.io/gh/kelsoncm/django-suap-auth/branch/main/graph/badge.svg)](https://codecov.io/gh/kelsoncm/django-suap-auth)

Backend de autenticação OAuth2 do Django para **SUAP** (Sistema Unificado de Administração Pública), o sistema de gestão acadêmica do [IFRN](https://www.ifrn.edu.br), hospedado em [suap.ifrn.edu.br](https://suap.ifrn.edu.br).

## Instalação

```bash
uv add django-suap-auth
# ou com pip:
# pip install django-suap-auth
```

## Início Rápido

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_suap_auth",
]

AUTHENTICATION_BACKENDS = [
    "django_suap_auth.backends.SuapAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SUAP_AUTH = {
    "CLIENT_ID": "your-client-id",
    "CLIENT_SECRET": "your-client-secret",
    "REDIRECT_URI": "https://yourapp.example.com/auth/suap/callback/",
    "SCOPES": ["identificacao", "email"],  # opcional
}
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/login/"
```

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("auth/suap/", include("django_suap_auth.urls")),
    ...
]
```

```html
<!-- template -->
<a href="{% url 'suap_auth:login' %}">Login com SUAP</a>
```

## Escopos Disponíveis

| Escopo | Descrição |
|--------|-----------|
| `identificacao` | Identificação básica (matricula, nome, campus) |
| `email` | Endereço de email |
| `documentos_pessoais` | Documentos pessoais (CPF, RG) |
| `dados_academicos` | Dados acadêmicos (curso, notas, situação) |
| `dados_pessoais` | Dados pessoais (data de nascimento, nacionalidade) |
| `reitoria` | Dados de nível institucional |

## Documentação

Documentação completa disponível no diretório [`docs/`](docs/) e nas GitHub Pages do projeto.

## Licença

MIT © 2026 kelsoncm

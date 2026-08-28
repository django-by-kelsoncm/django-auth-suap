=========================
Personificação de Usuário
=========================

O submódulo ``django_suap_auth.impersonation`` provê recursos de personificação (impersonation) de usuários para permitir que superusuários simulem a sessão de outros usuários durante procedimentos de suporte e testes.

Instalação
==========

Adicione ``django_suap_auth.impersonation`` ao seu ``INSTALLED_APPS`` em ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "django_suap_auth",
        "django_suap_auth.impersonation",
    ]

Rotas e Views
=============

Inclua as URLs de personificação no seu arquivo ``urls.py``:

.. code-block:: python

    from django.urls import include, path

    urlpatterns = [
        path("auth/impersonation/", include("django_suap_auth.impersonation.urls")),
    ]

Views disponíveis:

- ``ImpersonateView`` (rota ``impersonate/<str:username>/`` ou ``impersonate/`` com parâmetro query/POST):
  Inicia a personificação do usuário. Restrita a superusuários e impede a personificação de outros superusuários ou personificações aninhadas.
- ``StopImpersonatingView`` (rota ``stop-impersonating/``):
  Encerra a personificação ativa na sessão.

Helpers
=======

O submódulo fornece as seguintes funções utilitárias:

.. code-block:: python

    from django_suap_auth.impersonation.helpers import get_active_user, is_impersonating

    # Retorna o objeto User personificado se a sessão for de personificação ativa;
    # caso contrário, retorna request.user.
    user = get_active_user(request)

    # Retorna True se a requisição atual possui uma personificação ativa.
    personificando = is_impersonating(request)

Context Processor
=================

Para utilizar as variáveis no contexto de templates, adicione o context processor em ``settings.py``:

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "context_processors": [
                    # ...
                    "django_suap_auth.impersonation.context_processors.impersonation",
                ],
            },
        },
    ]

Variáveis injetadas no contexto de template:

- ``active_user``: Usuário ativo (considerando a personificação).
- ``is_impersonating``: Booleano indicando se a sessão atual é de personificação.

=====================
Endpoints JWT do SUAP
=====================

O SUAP disponibiliza três endpoints para autenticação baseada em JSON Web Tokens (JWT):

- ``/api/token/pair``: Obtenção do par de tokens (Access e Refresh) a partir de usuário e senha.
- ``/api/token/refresh``: Renovação do token de acesso a partir de um token de refresh válido.
- ``/api/token/verify``: Verificação da validade de um token JWT.

O ``django-suap-auth`` implementa entrypoints nativos do Django para estes endpoints, **sem necessidade de bibliotecas externas** como Django REST Framework (DRF) ou Django Ninja.

A ativação destes endpoints no seu projeto é **completamente opcional**.

Ativação Opcional de Rotas
==========================

Opção 1: Incluir via ``django_suap_auth.jwt_urls``
--------------------------------------------------

No seu ``urls.py`` principal, monte o módulo ``django_suap_auth.jwt_urls`` sob o prefixo desejado:

.. code-block:: python

   # urls.py
   from django.urls import include, path

   urlpatterns = [
       # Fluxo OAuth2 padrão (login, callback)
       path("auth/suap/", include("django_suap_auth.urls")),

       # Entrypoints JWT (opcional)
       path("api/token/", include("django_suap_auth.jwt_urls")),
   ]

Desta forma, as seguintes rotas ficarão disponíveis no seu projeto:

- ``POST /api/token/pair`` (ou ``/api/token/pair/``)
- ``POST /api/token/refresh`` (ou ``/api/token/refresh/``)
- ``POST /api/token/verify`` (ou ``/api/token/verify/``)

Opção 2: Incluir via ``django_suap_auth.api_urls``
--------------------------------------------------

Se preferir incluir direto na raiz do projeto:

.. code-block:: python

   urlpatterns = [
       path("", include("django_suap_auth.api_urls")),
   ]

Opção 3: Importação Direta das Views
------------------------------------

Você também pode registrar as views individualmente em qualquer rota customizada:

.. code-block:: python

   from django.urls import path
   from django_suap_auth.jwt_views import (
       SuapTokenPairView,
       SuapTokenRefreshView,
       SuapTokenVerifyView,
   )

   urlpatterns = [
       path("custom/jwt/pair/", SuapTokenPairView.as_view(), name="jwt_pair"),
       path("custom/jwt/refresh/", SuapTokenRefreshView.as_view(), name="jwt_refresh"),
       path("custom/jwt/verify/", SuapTokenVerifyView.as_view(), name="jwt_verify"),
   ]

Detalhes dos Endpoints
======================

1. Obter Par de Tokens (``/api/token/pair``)
--------------------------------------------

- **Método**: ``POST``
- **Content-Type**: ``application/json``
- **Corpo da requisição**:

.. code-block:: json

   {
     "username": "1234567",
     "password": "sua-senha-suap"
   }

- **Resposta de Sucesso (200 OK)**:

.. code-block:: json

   {
     "access": "eyJhbGciOi...",
     "refresh": "eyJhbGciOi...",
     "username": "1234567"
   }

- **Resposta de Erro (401 Unauthorized)**:

.. code-block:: json

   {
     "detail": "No active account found with the given credentials",
     "code": "authentication_failed"
   }

2. Atualizar Token (``/api/token/refresh``)
-------------------------------------------

- **Método**: ``POST``
- **Content-Type**: ``application/json``
- **Corpo da requisição**:

.. code-block:: json

   {
     "refresh": "eyJhbGciOi..."
   }

- **Resposta de Sucesso (200 OK)**:

.. code-block:: json

   {
     "access": "eyJhbGciOi...",
     "refresh": "eyJhbGciOi..."
   }

3. Verificar Token (``/api/token/verify``)
------------------------------------------

- **Método**: ``POST``
- **Content-Type**: ``application/json``
- **Corpo da requisição**:

.. code-block:: json

   {
     "token": "eyJhbGciOi..."
   }

- **Resposta de Sucesso (200 OK)**:

.. code-block:: json

   {}

4. Consumir Dados da API SUAP (``/api/rh/eu/`` ou ``/api/token/user-info``)
---------------------------------------------------------------------------

- **Método**: ``GET`` ou ``POST``
- **Header**: ``Authorization: Bearer <access_token>``
- **Corpo da requisição (opcional para POST)**:

.. code-block:: json

   {
     "token": "eyJhbGciOi...",
     "endpoint": "/api/rh/eu/"
   }

- **Resposta de Sucesso (200 OK)**:

.. code-block:: json

   {
     "identificacao": "2080882",
     "nome_usual": "Kelson Medeiros",
     "email": "kelson.medeiros@ifrn.edu.br",
     "campus": "ZL",
     "tipo_usuario": "Servidor (Técnico-Administrativo)"
   }

Uso Programático via Python
===========================

Você também pode utilizar os métodos de JWT diretamente através do cliente:

.. code-block:: python

   from django_suap_auth.client import SuapClient

   client = SuapClient(base_url="https://suap.ifrn.edu.br")

   # Obter tokens
   status, data = client.obtain_token_pair("username", "password")
   access_token = data.get("access")

   # Renovar token
   status, data = client.refresh_token("refresh_token")

   # Verificar token
   status, data = client.verify_token("access_token")

   # Consumir dados da API com o access token JWT
   user_info = client.get_endpoint_data(access_token, "/api/rh/eu/")

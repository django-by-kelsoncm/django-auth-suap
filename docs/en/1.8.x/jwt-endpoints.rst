====================
SUAP JWT Endpoints
====================

SUAP provides three endpoints for JSON Web Token (JWT) based authentication:

- ``/api/token/pair``: Obtain token pair (Access and Refresh) using username and password.
- ``/api/token/refresh``: Renew access token using a valid refresh token.
- ``/api/token/verify``: Verify the validity of a JWT token.

``django-suap-auth`` provides an optional sub-application ``django_suap_auth.jwt`` (following the same modular design pattern as ``django_suap_auth.profile``) to serve these endpoints natively in Django, **without requiring third-party libraries** such as Django REST Framework (DRF) or Django Ninja.

Enabling this sub-application in your project is **completely optional**.

Optional Route Activation
=========================

Step 1: Register Sub-Application in ``INSTALLED_APPS``
------------------------------------------------------

In your ``settings.py`` file:

.. code-block:: python

   INSTALLED_APPS = [
       ...
       "django_suap_auth",
       "django_suap_auth.jwt",  # Activation of JWT sub-application
   ]

Step 2: Include Sub-Application URLs
------------------------------------

Option 1: Include via ``django_suap_auth.jwt.urls`` (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your main ``urls.py``, mount the ``django_suap_auth.jwt.urls`` module under your desired prefix:

.. code-block:: python

   # urls.py
   from django.urls import include, path

   urlpatterns = [
       # Standard OAuth2 flow (login, callback)
       path("auth/suap/", include("django_suap_auth.urls")),

       # Sub-application JWT entrypoints (optional)
       path("api/token/", include("django_suap_auth.jwt.urls")),
   ]

This makes the following routes available in your application:

- ``POST /api/token/pair/``
- ``POST /api/token/refresh/``
- ``POST /api/token/verify/``
- ``GET/POST /api/token/user-info/``
- ``GET/POST /api/token/rh/eu/``

Option 2: Direct Views Import
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also register sub-application views individually on custom routes:

.. code-block:: python

   from django.urls import path
   from django_suap_auth.jwt.views import (
       SuapTokenPairView,
       SuapTokenRefreshView,
       SuapTokenVerifyView,
   )

   urlpatterns = [
       path("custom/jwt/pair/", SuapTokenPairView.as_view(), name="jwt_pair"),
       path("custom/jwt/refresh/", SuapTokenRefreshView.as_view(), name="jwt_refresh"),
       path("custom/jwt/verify/", SuapTokenVerifyView.as_view(), name="jwt_verify"),
   ]

Endpoint Details
================

1. Obtain Token Pair (``/api/token/pair``)
------------------------------------------

- **Method**: ``POST``
- **Content-Type**: ``application/json``
- **Request Body**:

.. code-block:: json

   {
     "username": "1234567",
     "password": "your-suap-password"
   }

- **Success Response (200 OK)**:

.. code-block:: json

   {
     "access": "eyJhbGciOi...",
     "refresh": "eyJhbGciOi...",
     "username": "1234567"
   }

- **Error Response (401 Unauthorized)**:

.. code-block:: json

   {
     "detail": "No active account found with the given credentials",
     "code": "authentication_failed"
   }

2. Refresh Token (``/api/token/refresh``)
-----------------------------------------

- **Method**: ``POST``
- **Content-Type**: ``application/json``
- **Request Body**:

.. code-block:: json

   {
     "refresh": "eyJhbGciOi..."
   }

- **Success Response (200 OK)**:

.. code-block:: json

   {
     "access": "eyJhbGciOi...",
     "refresh": "eyJhbGciOi..."
   }

3. Verify Token (``/api/token/verify``)
---------------------------------------

- **Method**: ``POST``
- **Content-Type**: ``application/json``
- **Request Body**:

.. code-block:: json

   {
     "token": "eyJhbGciOi..."
   }

- **Success Response (200 OK)**:

.. code-block:: json

   {}

4. Consume SUAP API Data (``/api/token/user-info`` or ``/api/token/rh/eu``)
----------------------------------------------------------------------------

- **Method**: ``GET`` or ``POST``
- **Header**: ``Authorization: Bearer <access_token>``
- **Request Body (optional for POST)**:

.. code-block:: json

   {
     "token": "eyJhbGciOi...",
     "endpoint": "/api/rh/eu/"
   }

- **Success Response (200 OK)**:

.. code-block:: json

   {
     "identificacao": "2080882",
     "nome_usual": "Kelson Medeiros",
     "email": "kelson.medeiros@ifrn.edu.br",
     "campus": "ZL",
     "tipo_usuario": "Servidor (Técnico-Administrativo)"
   }

Programmatic Python Usage
=========================

You can also use JWT methods directly via the client:

.. code-block:: python

   from django_suap_auth.client import SuapClient

   client = SuapClient(base_url="https://suap.ifrn.edu.br")

   # Obtain tokens
   status, data = client.obtain_token_pair("username", "password")
   access_token = data.get("access")

   # Refresh token
   status, data = client.refresh_token("refresh_token")

   # Verify token
   status, data = client.verify_token("access_token")

   # Consume API data with JWT access token
   user_info = client.get_endpoint_data(access_token, "/api/rh/eu/")

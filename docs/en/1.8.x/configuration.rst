===========================
SUAP OAuth2 Configuration
===========================

Basic Configuration
===================

In your ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'your-client-id',
       'CLIENT_SECRET': 'your-client-secret',
       'REDIRECT_URI': 'https://your-application.com/auth/suap/callback/',
   }

Configuration Options
=====================

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Key
     - Default
     - Description
   * - ``CLIENT_ID``
     - *required*
     - SUAP Application Client ID
   * - ``CLIENT_SECRET``
     - *required*
     - SUAP Application Client Secret
   * - ``REDIRECT_URI``
     - *required*
     - Callback URL registered in SUAP
   * - ``BASE_URL``
     - ``"https://suap.ifrn.edu.br"``
     - Base URL of the SUAP server
   * - ``SCOPES``
     - ``["identificacao", "email"]``
     - OAuth2 requested scopes
   * - ``USER_LOOKUP_FIELD``
     - ``"username"``
     - Field of the ``User`` model used as lookup key
   * - ``USER_ATTR_MAP``
     - see :doc:`attribute-mapping`
     - Dictionary of attribute mapping rules
   * - ``USER_INFO_FETCHERS``
     - ``["django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher"]``
     - List of fetchers executed in the Chain of Responsibility
   * - ``USER_INFO_ENDPOINTS``
     - ``["/api/rh/eu/"]``
     - List of SUAP endpoints to query and merge
   * - ``USER_INFO_MAPPERS``
     - ``["django_suap_auth.mappers.DefaultAttrMapUserMapper"]``
     - List of mappers executed in the Chain of Responsibility
   * - ``USER_JSON_FIELD``
     - ``None``
     - ``JSONField`` field to store raw SUAP response
   * - ``DIRECT_REDIRECT``
     - ``True``
     - Direct redirect to SUAP or intermediate login page
   * - ``CREATE_USER``
     - ``True``
     - If ``False``, does not create new users and raises an exception
   * - ``USER_DEFAULTS``
     - ``{"is_active": True}``
     - Default values assigned when creating a new user
   * - ``FIRST_USER_DEFAULTS``
     - ``{"is_staff": True, "is_superuser": True}``
     - Additional values applied only to the first created user in the database.
   * - ``UPDATE_FIELDS_ON_CREATE``
     - ``None``
     - List of mapped fields saved on creation (``None`` = all)
   * - ``UPDATE_FIELDS_ON_LOGIN``
     - ``None``
     - List of mapped fields synchronized on each login (``None`` = all)
   * - ``BACKEND``
     - ``"django_suap_auth.backends.SuapAuthBackend"``
     - Authentication backend class path

Complete Example with Multiple Endpoints and Mappers
====================================================

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'your-client-id',
       'CLIENT_SECRET': 'your-client-secret',
       'REDIRECT_URI': 'https://your-application.com/auth/suap/callback/',
       'USER_INFO_ENDPOINTS': [
           "/api/rh/eu/",
           "/api/rh/meus-dados/",
           {
               "endpoint": "/api/rh/meus-vinculos/",
               "namespace": "vinculos",
               "extract_list": "results",
           },
       ],
       'USER_INFO_MAPPERS': [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
           "my_app.mappers.CustomProfileUserMapper",
       ],
       'USER_ATTR_MAP': {
           "username": "identificacao",
           "email": "email",
           "rg": "rg",
           "cargo": "vinculo.cargo",
           "setor": "vinculo.setor_suap",
           "foto": {
               "key": "url_foto_75x100",
               "transform": "django_suap_auth.transformers.fetch_image_file",
           },
           "is_servidor": lambda info: any(v.get("tipo") == "servidor" for v in info.get("vinculos", [])),
       },
   }

User Creation Control
=====================

By default, the library automatically creates a user in Django on their first login via SUAP. This behavior is fully configurable:

1. Disable Automatic Creation via Configuration
-----------------------------------------------

If the ``CREATE_USER`` option is set to ``False``, login will be denied for users who do not have a pre-existing local account in Django, raising a ``django_suap_auth.exceptions.SuapUserNotAllowedError`` exception:

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'your-client-id',
       'CLIENT_SECRET': 'your-client-secret',
       'REDIRECT_URI': 'https://your-application.com/auth/suap/callback/',
       'CREATE_USER': False,  # Disables automatic user creation on login
   }

2. First User as Superuser (`FIRST_USER_DEFAULTS`)
--------------------------------------------------

By default, if no user exists in the database at the moment of the first login, the first created user automatically receives ``is_staff = True`` and ``is_superuser = True`` (via ``FIRST_USER_DEFAULTS = {"is_staff": True, "is_superuser": True}``).

To disable this automatic promotion of the first user, set the key to ``None`` in your ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'your-client-id',
       'CLIENT_SECRET': 'your-client-secret',
       'REDIRECT_URI': 'https://your-application.com/auth/suap/callback/',
       'FIRST_USER_DEFAULTS': None,  # First created user will not be staff/superuser
   }

3. Dynamic Decision via Custom Backend
--------------------------------------

To apply dynamic conditional rules during login (e.g. allowing user registration only for employees or specific link types), subclass ``SuapAuthBackend`` or ``SuapProfileAuthBackend`` and override ``get_or_create_user`` or ``create_user``:

.. code-block:: python

   from django_suap_auth.profile.backends import SuapProfileAuthBackend
   from django_suap_auth.exceptions import SuapUserNotAllowedError

   class CustomSuapAuthBackend(SuapProfileAuthBackend):
       def get_or_create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
           raw_info = mapped_attrs.get("suap_data", {})
           # Example: only allow automatic creation for Staff/Employees
           if raw_info.get("tipo_vinculo") != "Servidor":
               raise SuapUserNotAllowedError("Automatic creation allowed only for staff members.")

           return super().get_or_create_user(lookup_field, lookup_value, mapped_attrs, cfg)

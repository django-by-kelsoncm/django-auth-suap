====================================================
Mappers (User Attribute Mapping)
====================================================

``django-suap-auth`` uses the **Chain of Responsibility** pattern to map the raw user info dictionary (``user_info``) obtained by fetchers to Django ``User`` model fields.

How Mappers Work
================

The mapper chain (``USER_INFO_MAPPERS``) runs immediately after fetchers complete. Each mapper receives the accumulated ``user_info`` dictionary and the model attributes dictionary ``attrs``, adding or modifying field/value pairs.

.. code-block:: text

   [accumulated user_info] ──> Mapper 1 (DefaultAttrMapUserMapper)
                                   │ attrs = {'username': '...', 'email': '...'}
                                   ▼
                               Mapper 2 (Custom Mapper / Permissions)
                                   │ final attrs
                                   ▼
                               SuapAuthBackend (get_or_create)

Configuration: ``USER_INFO_MAPPERS``
====================================

In ``settings.py``, configure the list of mappers in ``SUAP_AUTH``:

.. code-block:: python

   SUAP_AUTH = {
       # ...
       "USER_INFO_MAPPERS": [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
           "my_app.mappers.ProfileUserMapper",
       ],
   }

Default Mapper: ``DefaultAttrMapUserMapper``
============================================

The default mapper interprets the rules defined in the ``USER_ATTR_MAP`` dictionary in ``SUAP_AUTH``.

Rule Formats in ``USER_ATTR_MAP``
---------------------------------

1. Direct Mapping or Dotted Path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_ATTR_MAP": {
       "username": "identificacao",
       "email": "email",
       "cargo": "vinculo.cargo",  # extracts from nested dictionary user_info['vinculo']['cargo']
   }

2. Complete Raw Dictionary (``fulljson``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_ATTR_MAP": {
       "suap_data": "fulljson",  # assigns the entire user_info dict to field 'suap_data'
   }

3. Splitting Name into Two Fields (Tuple)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_ATTR_MAP": {
       ("first_name", "last_name"): "nome_registro",
       # "João Silva Santos" -> first_name="João Silva", last_name="Santos"
   }

4. Lambdas and Custom Callables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_ATTR_MAP": {
       "is_staff": lambda info: info.get("tipo_vinculo") == "Servidor",
   }

5. Specification with Transformers and Default Values (dict spec)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_ATTR_MAP": {
       "cpf": {
           "key": "cpf",
           "transform": "django_suap_auth.transformers.format_cpf",
       },
       "data_nascimento": {
           "key": "data_nascimento",
           "transform": "django_suap_auth.transformers.parse_date",
       },
       "foto": {
           "key": "url_foto_75x100",
           "transform": "django_suap_auth.transformers.fetch_image_file",
       },
       "status": {
           "key": "situacao",
           "default": "Active",
       },
   }

Built-in Transformers (``django_suap_auth.transformers``)
==========================================================

The package provides the following built-in transformation functions:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Transformer
     - Description
   * - ``fetch_image_file(value, suap_info=None)``
     - Downloads an image from URL and returns a ``ContentFile`` for ``ImageField``/``FileField`` fields.
   * - ``parse_date(value, suap_info=None)``
     - Converts ISO date string (``YYYY-MM-DD``) to ``datetime.date``.
   * - ``format_cpf(value, suap_info=None)``
     - Formats an 11-digit string into standard format ``"XXX.XXX.XXX-XX"``.
   * - ``to_upper(value, suap_info=None)``
     - Converts string to uppercase.
   * - ``to_lower(value, suap_info=None)``
     - Converts string to lowercase.
   * - ``to_bool(value, suap_info=None)``
     - Converts value to boolean (``True``/``False``).

Creating a Custom Mapper
========================

To create a custom mapper, inherit from ``BaseUserMapper`` (or alias ``BaseSuapUserMapper``) and override ``map_attributes``:

.. code-block:: python

   # my_app/mappers.py
   from django_suap_auth.mappers import BaseUserMapper

   class CustomProfileUserMapper(BaseUserMapper):
       """Mapper to set staff flags and permissions based on SUAP profile."""

       def map_attributes(self, user_info, attrs=None):
           attrs = super().map_attributes(user_info, attrs)

           # Example: grant staff permission to IFRN employees
           if user_info.get("tipo_usuario") == "Servidor":
               attrs["is_staff"] = True

           return attrs

Registering the Custom Mapper
-----------------------------

.. code-block:: python

   # settings.py
   SUAP_AUTH = {
       # ...
       "USER_INFO_MAPPERS": [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
           "my_app.mappers.CustomProfileUserMapper",
       ],
   }

Mapper API Utility Functions
============================

- ``get_user_info_mappers(cfg=None)``: instantiates and returns the configured mappers list.
- ``run_user_info_mapper_chain(user_info, attr_map=None, cfg=None)``: runs the mapper chain and returns the final ``attrs`` dictionary for the user model.

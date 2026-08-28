=============================================================
Mapping SUAP Attributes to the Django User Model
=============================================================

The ``USER_ATTR_MAP`` dictionary defines how fields returned by SUAP APIs are saved to the Django ``User`` model (whether standard or custom via ``AUTH_USER_MODEL``).

Default Mapping
===============

.. code-block:: python

   SUAP_AUTH = {
       # ...
       'USER_ATTR_MAP': {
           'username': 'identificacao',
           'email': 'email',
           ('first_name', 'last_name'): 'nome_registro',
       },
   }

Supported Mapping Formats
=========================

1. Simple or Nested Field (Dotted Path)
---------------------------------------

.. code-block:: python

   'USER_ATTR_MAP': {
       'username': 'identificacao',
       'email': 'email',
       'cpf': 'dados_pessoais.cpf',   # extracts from nested dictionary
       'suap_raw': 'fulljson',        # assigns full user_info dictionary to field
   }

2. Splitting Name into Two Fields (Tuple)
-----------------------------------------

When the mapping key is a **tuple**, the value returned by SUAP is split at the last space:

.. code-block:: python

   ('first_name', 'last_name'): 'nome_registro'
   # "João Silva Santos" → first_name="João Silva", last_name="Santos"
   # "João"              → first_name="João", last_name=""

3. Custom Lambdas and Callables
-------------------------------

You can pass a ``callable`` or ``lambda`` that receives the complete SUAP user info dictionary (``suap_user_info``):

.. code-block:: python

   'USER_ATTR_MAP': {
       'username': 'identificacao',
       'full_name': lambda info: f"{info.get('primeiro_nome', '')} {info.get('ultimo_nome', '')}".strip(),
       'is_student': lambda info: info.get('tipo_vinculo') == 'Aluno',
   }

4. Specification Dictionaries with Transformers and Defaults (dict spec)
-------------------------------------------------------------------------

Allows defining the source key, default value (``default``), and a transformation function (``transform``):

.. code-block:: python

   'USER_ATTR_MAP': {
       'username': 'identificacao',
       'cpf': {
           'key': 'cpf',
           'transform': 'django_suap_auth.transformers.format_cpf',
       },
       'data_nascimento': {
           'key': 'data_nascimento',
           'transform': 'django_suap_auth.transformers.parse_date',
       },
       'campus': {
           'key': 'vinculo.campus',
           'default': 'Main Campus',
       },
   }

Mapping Photos (URL vs Download for ImageField)
===============================================

SUAP returns the photo URL in the ``url_foto_75x100`` field.

Case A: Map URL only (CharField / URLField)
-------------------------------------------

.. code-block:: python

   'USER_ATTR_MAP': {
       'foto_url': 'url_foto_75x100',
   }

Case B: Download Photo and Save to ImageField / FileField
---------------------------------------------------------

Use the ``fetch_image_file`` transformer provided by the package:

.. code-block:: python

   'USER_ATTR_MAP': {
       'foto': {
           'key': 'url_foto_75x100',
           'transform': 'django_suap_auth.transformers.fetch_image_file',
       },
   }

Or via a custom lambda:

.. code-block:: python

   from django_suap_auth.transformers import fetch_image_file

   'USER_ATTR_MAP': {
       'foto': lambda info: fetch_image_file(info.get('url_foto_75x100')),
   }

Built-in Transformation Utilities (``django_suap_auth.transformers``)
======================================================================

The package provides the following built-in functions:

- ``fetch_image_file(value, suap_info=None)``: downloads the image from the given URL and returns a Django ``ContentFile`` ready to be saved in an ``ImageField`` / ``FileField``.
- ``parse_date(value, suap_info=None)``: converts ISO date string (``YYYY-MM-DD``) to ``datetime.date``.
- ``format_cpf(value, suap_info=None)``: formats an 11-digit string to standard ``"XXX.XXX.XXX-XX"``.
- ``to_upper(value, suap_info=None)`` / ``to_lower(value, suap_info=None)``: converts text case.
- ``to_bool(value, suap_info=None)``: converts various values to boolean.

Custom Class-Based Mapper (``USER_MAPPER``)
===========================================

For complex scenarios (such as recording profiles in linked tables), you can implement a custom class derived from ``BaseSuapUserMapper``:

.. code-block:: python

   # mappers.py
   from django_suap_auth.mappers import BaseSuapUserMapper

   class CustomSuapUserMapper(BaseSuapUserMapper):
       def map_attributes(self, user_info, attr_map=None):
           attrs = super().map_attributes(user_info, attr_map)
           attrs['is_servidor'] = (user_info.get('tipo_vinculo') == 'Servidor')
           return attrs

And activate it in your Django settings:

.. code-block:: python

   SUAP_AUTH = {
       # ...
       'USER_MAPPER': 'my_app.mappers.CustomSuapUserMapper',
   }

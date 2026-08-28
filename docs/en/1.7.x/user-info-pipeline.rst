==================================================
User Info Fetching and Mapping Pipeline
==================================================

``django-suap-auth`` uses the **Chain of Responsibility** design pattern for both data fetching (``USER_INFO_FETCHERS``) and attribute mapping (``USER_INFO_MAPPERS``) subsystems.

General Architecture
====================

.. figure:: user-info-pipeline.svg
   :alt: User info fetching and mapping pipeline architecture diagram
   :align: center
   :width: 320px

   General Architecture of the User Pipeline


1. Data Fetching Chain (``USER_INFO_FETCHERS``)
================================================

SUAP provides multiple API endpoints (``/api/rh/eu/``, ``/api/rh/meus-dados/``, ``/api/rh/meus-vinculos/``). The fetcher chain queries these endpoints and merges the resulting information into a single ``user_info`` dictionary.

Default Handler: ``DefaultEndpointsUserInfoFetcher``
----------------------------------------------------

Consumes the ``USER_INFO_ENDPOINTS`` list from ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       # List of SUAP endpoints to query and merge
       "USER_INFO_ENDPOINTS": [
           "/api/rh/eu/",          # Basic data merged at the root dictionary level
           "/api/rh/meus-dados/",  # Merges rg, filiacao, vinculo.cargo, etc.
           {
               "endpoint": "/api/rh/meus-vinculos/",
               "namespace": "vinculos",   # Injected under user_info['vinculos']
               "extract_list": "results", # Extracts list from paginated 'results' field
           },
           {
               "endpoint": "/api/rh/meu-vinculo/{id}/",
               "namespace": "detalhes_vinculos",
               "for_each": "vinculos",    # Iterates over each item in user_info['vinculos']
           },
       ],
   }

Creating a Custom Fetcher for External Sources
-----------------------------------------------

You can add handlers to the ``USER_INFO_FETCHERS`` chain to query internal HR systems, LDAP, or corporate databases:

.. code-block:: python

   # my_app/fetchers.py
   from django_suap_auth.fetchers import BaseUserInfoFetcher

   class ExternalLdapUserInfoFetcher(BaseUserInfoFetcher):
       def fetch(self, client, access_token, user_info=None):
           user_info = super().fetch(client, access_token, user_info)

           cpf = user_info.get("cpf")
           if cpf:
               # Enrich the dictionary with data from external source
               user_info["ldap"] = my_ldap_service.search_by_cpf(cpf)

           return user_info

Configuration in ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       "USER_INFO_FETCHERS": [
           "django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher",
           "my_app.fetchers.ExternalLdapUserInfoFetcher",
       ],
   }

2. Mapping Chain (``USER_INFO_MAPPERS``)
=========================================

After fetching, the mapper chain receives the unified ``user_info`` dictionary and builds the attributes for the Django user model.

Default Handler: ``DefaultAttrMapUserMapper``
---------------------------------------------

Applies the rules configured in ``USER_ATTR_MAP``:

.. code-block:: python

   SUAP_AUTH = {
       "USER_INFO_MAPPERS": [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
       ],
       "USER_ATTR_MAP": {
           "username": "identificacao",
           "email": "email",
           "rg": "rg",
           "cargo": "vinculo.cargo",
           "foto": {
               "key": "url_foto_75x100",
               "transform": "django_suap_auth.transformers.fetch_image_file",
           },
           "is_servidor": lambda info: any(v.get("tipo") == "servidor" for v in info.get("vinculos", [])),
       },
   }

Creating a Custom Mapper
------------------------

To add complex logic or manipulate the user model attributes directly:

.. code-block:: python

   # my_app/mappers.py
   from django_suap_auth.mappers import BaseUserMapper

   class ProfileUserMapper(BaseUserMapper):
       def map_attributes(self, user_info, attrs=None):
           attrs = super().map_attributes(user_info, attrs)
           if user_info.get("ldap", {}).get("is_admin"):
               attrs["is_staff"] = True
           return attrs

Configuration in ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       "USER_INFO_MAPPERS": [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
           "my_app.mappers.ProfileUserMapper",
       ],
   }

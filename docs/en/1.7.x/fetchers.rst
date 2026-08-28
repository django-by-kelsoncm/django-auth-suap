=========================================
Fetchers (User Data Retrieval)
=========================================

``django-suap-auth`` uses the **Chain of Responsibility** pattern to retrieve and consolidate user profile data from multiple SUAP API endpoints or external systems.

How Fetchers Work
=================

When a user is authenticated via OAuth2, the ``access_token`` is acquired and the fetcher chain (``USER_INFO_FETCHERS``) is executed sequentially. Each fetcher receives the accumulated ``user_info`` dictionary and can enrich it with new data.

.. code-block:: text

   [Access Token] ──> Fetcher 1 (DefaultEndpointsUserInfoFetcher)
                          │ accumulated user_info
                          ▼
                      Fetcher 2 (Custom Fetcher / LDAP)
                          │ final user_info
                          ▼
                      Mapper Chain

Configuration: ``USER_INFO_FETCHERS``
=====================================

In ``settings.py``, configure the list of fetchers in ``SUAP_AUTH``:

.. code-block:: python

   SUAP_AUTH = {
       "CLIENT_ID": "your-client-id",
       "CLIENT_SECRET": "your-client-secret",
       "REDIRECT_URI": "https://your-app.com/auth/suap/callback/",
       "USER_INFO_FETCHERS": [
           "django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher",
           "my_app.fetchers.ExternalLdapUserInfoFetcher",
       ],
   }

Default Fetcher: ``DefaultEndpointsUserInfoFetcher``
====================================================

The default fetcher consumes the ``USER_INFO_ENDPOINTS`` list defined in ``SUAP_AUTH`` and executes HTTP requests for each endpoint.

Supported Endpoint Formats (``USER_INFO_ENDPOINTS``)
----------------------------------------------------

1. Simple Endpoint (String)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_INFO_ENDPOINTS": [
       "/api/rh/eu/",
       "/api/rh/meus-dados/",
   ]

Data returned at the root of JSON responses are merged directly into the root of the ``user_info`` dictionary.

2. Endpoint with Dynamic Formatting (String with ``{key}``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   "USER_INFO_ENDPOINTS": [
       "/api/rh/eu/",
       "/api/v2/alunos/{matricula}/",
   ]

Keys enclosed in braces ``{...}`` are substituted with existing values from ``user_info``.

3. Specification Dictionary (dict spec)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allows isolating responses under a *namespace*, extracting lists from paginated responses, or iterating over collections:

.. code-block:: python

   "USER_INFO_ENDPOINTS": [
       "/api/rh/eu/",
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
   ]

Creating a Custom Fetcher
=========================

To create a custom fetcher, inherit from ``BaseUserInfoFetcher`` and override the ``fetch`` method:

.. code-block:: python

   # my_app/fetchers.py
   from django_suap_auth.fetchers import BaseUserInfoFetcher

   class ExternalLdapUserInfoFetcher(BaseUserInfoFetcher):
       """Fetcher that retrieves additional information from corporate LDAP using the user's CPF."""

       def fetch(self, client, access_token, user_info=None):
           user_info = super().fetch(client, access_token, user_info)

           cpf = user_info.get("cpf")
           if cpf:
               # Query external service
               user_info["ldap_data"] = my_ldap_service.search_by_cpf(cpf)

           return user_info

Registering the Custom Fetcher
------------------------------

.. code-block:: python

   # settings.py
   SUAP_AUTH = {
       # ...
       "USER_INFO_FETCHERS": [
           "django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher",
           "my_app.fetchers.ExternalLdapUserInfoFetcher",
       ],
   }

Fetcher API Utility Functions
=============================

- ``get_user_info_fetchers(cfg=None)``: instantiates and returns the list of configured fetcher objects.
- ``run_user_info_fetcher_chain(client, access_token, cfg=None)``: runs the entire fetcher chain and returns the final ``user_info`` dictionary.

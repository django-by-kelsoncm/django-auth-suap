================
django-suap-auth
================

Django OAuth2 authentication backend for **SUAP** (Unified Public Administration Management System), the academic management system of IFRN.

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   installation
   configuration
   profile-models
   impersonation
   jwt-endpoints
   scopes
   attribute-mapping
   user-info-pipeline
   fetchers
   mappers
   auth-flow
   sandboxes
   development
   release

Features
========

- OAuth2 Authorization Code Flow with SUAP
- Optional JWT authentication endpoints (``/api/token/pair``, ``/api/token/refresh``, ``/api/token/verify``)
- Submodule ``django_suap_auth.profile`` with built-in profile models (``Perfil``, ``DadosBrutos``, ``Vinculo``)
- Submodule ``django_suap_auth.impersonation`` for user impersonation workflows
- Configurable scopes (``identificacao``, ``email``, ``documentos_pessoais``, ``dados_academicos``, ``dados_pessoais``, ``reitoria``)
- Flexible attribute mapping from SUAP response to Django User model fields
- Optional JSON field storage for complete SUAP responses
- Configurable intermediate login page (``SUAP_AUTH['DIRECT_REDIRECT']``)
- CSRF protection via state parameter validation

Quick Links
===========

- :doc:`Installation <installation>`
- :doc:`Configuration <configuration>`
- :doc:`Profile Models <profile-models>`
- :doc:`Impersonation <impersonation>`
- :doc:`JWT Endpoints <jwt-endpoints>`
- :doc:`Scopes <scopes>`
- :doc:`Attribute Mapping <attribute-mapping>`
- :doc:`User Info Pipeline <user-info-pipeline>`
- :doc:`Fetchers <fetchers>`
- :doc:`Mappers <mappers>`
- :doc:`Authentication Flow <auth-flow>`
- :doc:`Sandboxes <sandboxes>`
- :doc:`Development <development>`
- :doc:`Release Process <release>`

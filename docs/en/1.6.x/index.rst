================
django-suap-auth
================

Django OAuth2 authentication backend for **SUAP** (Unified Public Administration Management System), the academic management system of IFRN.

Introduction
============

**django-suap-auth** is a Python/Django library designed to simplify and standardize authentication and user profile data retrieval between Django applications and **SUAP** (Unified Public Administration Management System) — the academic and administrative management platform used by the Federal Institute of Rio Grande do Norte (IFRN).

The package abstracts the complexity of communicating via the **OAuth2 Authorization Code Flow** protocol with SUAP's identity provider. It automatically handles exchanging authorization codes for access tokens, querying SUAP user data APIs, and mapping those attributes onto the Django ``User`` model.

Beyond basic login integration, the library provides:

* **Extensible Data Pipeline**: A *Chain of Responsibility* architecture featuring customizable fetchers and mappers to retrieve data from various SUAP API endpoints and map attributes onto the user model.
* **Profile & Raw Data Submodule (``django_suap_auth.profile``)**: Ready-to-use Django models (``Perfil``, ``DadosBrutos``, ``Vinculo``) to store academic/staff roles and persist full raw JSON responses from SUAP.
* **Native JWT Authentication (``django_suap_auth.jwt``)**: Built-in endpoints for issuing and validating JWT tokens (without requiring heavy third-party REST frameworks).

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   installation
   configuration
   profile-models
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

============
Installation
============

Requirements
============

- Python 3.10+
- Django 5.2+

Install from PyPI
=================

With ``uv`` (recommended):

.. code-block:: bash

   uv add django-suap-auth

Or with ``pip``:

.. code-block:: bash

   pip install django-suap-auth

Add to INSTALLED_APPS
=====================

In your ``settings.py`` file:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "django_suap_auth",
   ]

Configure URLs
==============

In your ``urls.py`` file:

.. code-block:: python

   # urls.py
   from django.urls import path, include

   urlpatterns = [
       path("auth/suap/", include("django_suap_auth.urls")),
   ]

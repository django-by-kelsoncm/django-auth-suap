==========
Instalação
==========

Requisitos
==========

- Python 3.10+
- Django 5.2+

Instalar do PyPI
================

Com ``uv`` (recomendado):

.. code-block:: bash

   uv add django-suap-auth

Ou com ``pip``:

.. code-block:: bash

   pip install django-suap-auth

Adicionar a INSTALLED_APPS
==========================

No seu arquivo ``settings.py``:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "django_suap_auth",
   ]

Configurar URLs
===============

No seu arquivo ``urls.py``:

.. code-block:: python

   # urls.py
   from django.urls import path, include

   urlpatterns = [
       path("auth/suap/", include("django_suap_auth.urls")),
   ]

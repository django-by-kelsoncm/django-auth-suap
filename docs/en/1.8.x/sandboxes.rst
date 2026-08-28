=========
Sandboxes
=========

Two sandbox projects are included for manual functional testing. They are **not** included in the published PyPI package.

sandbox/django52
================

Django 5.2 sandbox.

.. code-block:: bash

   cd sandbox/django52
   cp .env.example .env
   # Edit .env with your SUAP credentials
   uv pip install -r requirements.txt # or pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver

sandbox/django60
================

Django 6.0 sandbox.

.. code-block:: bash

   cd sandbox/django60
   cp .env.example .env
   # Edit .env with your SUAP credentials
   uv pip install -r requirements.txt # or pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver

Comparing Django Versions
=========================

The two sandboxes allow comparing ``django-suap-auth`` behavior between Django 5.2 and 6.0. Both are configured identically and use the parent directory's package code.

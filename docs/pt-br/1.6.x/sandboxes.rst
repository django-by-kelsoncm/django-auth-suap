=========
Sandboxes
=========

Duas sandboxes estão incluídas para testes funcionais manuais. Elas **não** fazem parte do pacote PyPI publicado.

sandbox/django52
================

Sandbox Django 5.2.

.. code-block:: bash

   cd sandbox/django52
   cp .env.example .env
   # Edite .env com suas credenciais SUAP
   uv pip install -r requirements.txt # ou pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver

sandbox/django60
================

Sandbox Django 6.0.

.. code-block:: bash

   cd sandbox/django60
   cp .env.example .env
   # Edite .env com suas credenciais SUAP
   uv pip install -r requirements.txt # ou pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver

Comparando Versões do Django
============================

As duas sandboxes permitem comparar o comportamento do ``django-suap-auth`` entre Django 5.2 e 6.0. Ambas são configuradas de forma idêntica e usam o mesmo código do pacote do diretório pai.

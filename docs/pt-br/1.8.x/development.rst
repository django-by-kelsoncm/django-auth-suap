===============
Desenvolvimento
===============

Configuração
============

.. code-block:: bash

   git clone https://github.com/django-by-kelsoncm/django-auth-suap.git
   cd django-auth-suap
   uv pip install -e ".[dev]" # ou pip install -e ".[dev]"
   pre-commit install
   pre-commit install --hook-type pre-push

Executando Testes
=================

.. code-block:: bash

   pytest --cov=django_suap_auth --cov-report=term-missing

Estilo de Código
================

.. code-block:: bash

   ruff check .
   ruff format .

pre-commit
==========

O projeto usa hooks pre-commit:

- **pre-commit**: espaços em branco à direita, fixador de fim de arquivo, verificação yaml, lint/format ruff
- **pre-push**: pytest

Documentação
============

Para compilar e visualizar a documentação localmente:

.. code-block:: bash

   sphinx-build -b html docs site

Ou utilizando o ``Makefile`` na pasta ``docs/``:

.. code-block:: bash

   cd docs
   make html

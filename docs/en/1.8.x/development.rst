===========
Development
===========

Setup
=====

.. code-block:: bash

   git clone https://github.com/django-by-kelsoncm/django-auth-suap.git
   cd django-auth-suap
   uv pip install -e ".[dev]" # or pip install -e ".[dev]"
   pre-commit install
   pre-commit install --hook-type pre-push

Running Tests
=============

.. code-block:: bash

   pytest --cov=django_suap_auth --cov-report=term-missing

Code Style
==========

.. code-block:: bash

   ruff check .
   ruff format .

pre-commit
==========

The project uses pre-commit hooks:

- **pre-commit**: trailing whitespace, end-of-file fixer, yaml check, ruff lint/format
- **pre-push**: pytest

Documentation
=============

To build and view documentation locally:

.. code-block:: bash

   sphinx-build -b html docs/en/1.6.x docs/_build/html/en/1.6.x

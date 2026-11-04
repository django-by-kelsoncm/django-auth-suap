=============================
Exporting and Importing Users
=============================

The ``django_suap_auth.profile`` module can export users with their ``Perfil``, ``Vinculo`` and ``DadosBrutos`` to
JSON and import them into another environment. The typical use is reproducing a production case in a test
environment (e.g. rules that depend on ``suap_raw_data`` and ``suap_vinculos``).

.. warning::
   **Personal data.** The file contains CPF, RG, e-mails, birth date, parents' names and the full SUAP response.
   Use it only for support and testing, do not share or commit it, and delete it after use (LGPD).
   The library never logs the file contents.

Format
======

.. code-block:: json

   {
     "formato": "django-suap-auth/usuarios",
     "versao": 1,
     "exportado_em": "2026-11-04T12:00:00Z",
     "usuarios": [
       {
         "user": {"username": "20231234567", "first_name": "Maria", "last_name": "Aluna",
                  "email": "maria@academico.ifrn.edu.br", "is_active": true},
         "perfil": {"matricula": "20231234567", "cpf": "99988877766", "data_nascimento": "2005-03-01"},
         "vinculos": [{"suap_id": 1, "tipo": "Aluno", "campus": "CNAT", "ativo": true, "detalhamento": {}}],
         "dados_brutos": {"identificacao": "20231234567"}
       }
     ]
   }

- ``user`` carries only ``username``, ``first_name``, ``last_name``, ``email`` and ``is_active``. **Never** the
  password, ``is_staff``, ``is_superuser``, groups or permissions; the import rejects these fields.
- ``perfil`` and each ``vinculos`` item carry every model field except ``id`` and ``user``.
- ``dados_brutos`` is ``DadosBrutos.data``.
- ``versao`` changes when the format changes incompatibly; the import rejects unknown versions.
- A single user inside the envelope itself (``formato``, ``versao``, ``user``, ``perfil``...) is also accepted.

Import Rules
============

The import is transactional (all or nothing) and upserts by ``username``:

- **User**: new users get an unusable password and no admin flags; for existing users only names, e-mail and
  ``is_active`` are updated. Password, ``is_staff``, ``is_superuser``, groups and permissions never change.
- **Perfil**: created or updated with the given fields; a null or missing ``perfil`` keeps the current one.
- **Vinculos**: replaced by the file's list (an empty or missing list removes all).
- **Dados brutos**: replaced; a null or missing ``dados_brutos`` removes the current record.
- Unknown fields (e.g. from a newer library version) are ignored and listed as warnings.
- Validation errors point to the exact location, e.g. ``usuarios[0].perfil.data_nascimento: ...``.

Django Admin
============

Available in ``CustomUserAdmin`` (and admins extending it) **for superusers only**:

- **"Exportar (JSON) com perfil, vínculos e dados brutos"** action on the user list, which downloads
  ``usuarios-suap-YYYYMMDD-HHMMSS.json``.
- **"Importar usuários"** button on the list, opening ``<admin>/<app>/<user>/importar/``: upload the file, review the
  preview (create/update, profile, links, raw data and warnings) and confirm. Nothing is saved before confirming.
  10 MB limit per file.

Management Commands
===================

.. code-block:: bash

   # export one or more users (without -o, writes to standard output)
   python manage.py export_suap_user 20231234567 2080882 -o users.json

   # check what would be done, without saving
   python manage.py import_suap_user users.json --dry-run

   # import
   python manage.py import_suap_user users.json

Python API
==========

.. code-block:: python

   from django_suap_auth.profile import transfer

   text = transfer.para_json(transfer.exportar_usuarios(User.objects.filter(username="20231234567")))

   users = transfer.carregar_json(text)  # raises transfer.ImportacaoInvalida (attribute .erros)
   results = transfer.importar_usuarios(users, dry_run=False)

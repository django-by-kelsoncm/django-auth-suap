========================================================================
Built-in Profile Models (`django_suap_auth.profile`)
========================================================================

The ``django_suap_auth.profile`` submodule provides pre-built Django models to store SUAP profile data out of the box, eliminating the need to manually map fields in your projects.

Models Overview
===============

The submodule defines 3 main models:

1. ``Perfil``: 1-to-1 model linked to the Django ``User`` model (via ``user.suap_profile``). Stores personal, academic, and functional data.
2. ``DadosBrutos``: 1-to-1 model linked to ``User`` (via ``user.suap_raw_data``). Stores the complete JSON response returned by SUAP APIs in a ``JSONField``.
3. ``Vinculo``: 1-to-Many model linked to ``User`` (via ``user.suap_vinculos``). Stores the list of user affiliations with the institution (e.g. staff, student, intern).

Installation and Setup
======================

1. Add ``django_suap_auth.profile`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "django_suap_auth",
       "django_suap_auth.profile",
   ]

2. Enable the authentication backend with automatic profile synchronization in ``settings.py``:

.. code-block:: python

   AUTHENTICATION_BACKENDS = [
       "django_suap_auth.profile.backends.SuapProfileAuthBackend",
       "django.contrib.auth.backends.ModelBackend",
   ]

3. Run database migrations:

.. code-block:: bash

   python manage.py migrate

Attributes of ``Perfil`` Model by User Type
===========================================

The ``Perfil`` model gathers all attributes supported by SUAP APIs into a single table:

1. Common Attributes (Present in All Users)
-------------------------------------------

These attributes are shared by **Staff/Employees**, **Students**, and **External Users**:

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``suap_id``
     - IntegerField
     - SUAP internal user ID.
   * - ``matricula``
     - CharField
     - Functional or academic registration number.
   * - ``nome_usual``
     - CharField
     - Display/usual name in SUAP.
   * - ``nome_social``
     - CharField
     - Registered social name.
   * - ``cpf``
     - CharField
     - Formatted or numeric CPF.
   * - ``rg``
     - CharField
     - ID card number (RG) with issuing body.
   * - ``filiacao``
     - JSONField
     - List of parent/guardian names.
   * - ``data_nascimento``
     - DateField
     - Date of birth.
   * - ``naturalidade``
     - CharField
     - Birth city and state.
   * - ``tipo_sanguineo``
     - CharField
     - Blood type (e.g. A+, O-).
   * - ``sexo``
     - CharField
     - Sex ("M" or "F").
   * - ``passaporte``
     - CharField
     - Passport number (when applicable).
   * - ``campus``
     - CharField
     - Campus code or name.
   * - ``email_secundario``
     - EmailField
     - Personal/secondary email.
   * - ``email_google_classroom``
     - EmailField
     - Institutional Google Workspace email account.
   * - ``email_academico``
     - EmailField
     - Institutional email.
   * - ``email_preferencial``
     - EmailField
     - Preferred contact email.
   * - ``url_foto_75x100``
     - URLField
     - Profile picture URL (thumbnail).
   * - ``url_foto_150x200``
     - URLField
     - Profile picture URL (medium).
   * - ``tipo_usuario``
     - CharField
     - User type (e.g. Staff, Student, External User).
   * - ``tipo_vinculo``
     - CharField
     - Primary affiliation (e.g. Teacher, Administrative Staff).
   * - ``telefones_institucionais``
     - JSONField
     - List of contact phone numbers.
   * - ``curriculo_lattes``
     - CharField
     - Lattes CV URL or ID.
   * - ``settings``
     - JSONField
     - Dictionary with user interface and accessibility preferences.
   * - ``first_login``
     - DateTimeField
     - Timestamp of first login via SUAP.

2. Staff-Specific Attributes
----------------------------

Filled exclusively when the user is **Staff/Employee** (Teacher or Administrative):

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``categoria``
     - CharField
     - Functional category (e.g. "Docente", "Técnico-Administrativo").
   * - ``cargo``
     - CharField
     - Job title (e.g. "Professor EBTT", "IT Analyst").
   * - ``setor_suap``
     - CharField
     - SUAP department acronym.
   * - ``setor_siape``
     - CharField
     - SIAPE department code or description.
   * - ``jornada_trabalho``
     - CharField
     - Work schedule regime (e.g. "40 hours", "Exclusive Dedication").
   * - ``disciplina_ingresso``
     - CharField
     - Entry contest subject/area.

3. Student-Specific Attributes
------------------------------

Filled exclusively when the user is a **Student**:

.. list-table::
   :widths: 30 20 50
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``curso``
     - CharField
     - Enrolled course name.
   * - ``turno``
     - CharField
     - Student course shift (e.g. "Distance Learning", "Morning").
   * - ``matriz``
     - CharField
     - Curriculum matrix code/name.
   * - ``situacao``
     - CharField
     - Enrollment status (e.g. "Incomplete", "Enrolled", "Graduated").
   * - ``situacao_sistemica``
     - CharField
     - General systemic status in SUAP.
   * - ``ira``
     - CharField
     - Academic Performance Index (IRA).
   * - ``ingresso``
     - CharField
     - Entry term/period (e.g. "2021.1").
   * - ``periodo_referencia``
     - IntegerField
     - Current academic term.
   * - ``qtd_periodos``
     - IntegerField
     - Total number of course terms.
   * - ``data_migracao``
     - CharField
     - Student record migration date.
   * - ``impressao_digital``
     - BooleanField
     - Indicates if fingerprint is registered.
   * - ``emitiu_diploma``
     - BooleanField
     - Indicates if diploma was issued.
   * - ``matricula_regular``
     - BooleanField
     - Indicates if student enrollment is regular.
   * - ``educasenso``
     - CharField
     - Student code in Educacenso / INEP.
   * - ``cota_sistec``
     - CharField
     - Sistec quota code.
   * - ``cota_mec``
     - CharField
     - MEC quota code.
   * - ``linha_pesquisa``
     - CharField
     - Student research area (graduate / research).

4. External Users / Contractors
-------------------------------

For **External Users** or third-party contractors:
- Staff and Student attributes remain empty/null.
- ``tipo_usuario`` records ``"Usuário Externo"`` or ``"Prestador de Serviço"``.
- Basic identification, photos, emails, and CPF are synchronized in common attributes.

Automatic Synchronization
=========================

When using ``SuapProfileAuthBackend``, on every login (or user creation) the following actions run automatically:

1. A ``Perfil`` instance is created/updated for the user.
2. The complete JSON response from the SUAP API is saved in ``DadosBrutos`` (accessible via ``user.suap_raw_data.data``).
3. The affiliation list in ``Vinculo`` is synchronized (accessible via ``user.suap_vinculos.all()``).
4. ``first_login`` is populated with current datetime on first login.

Computed Properties and Accessibility
=====================================

The ``Perfil`` model exposes several computed properties:

- ``show_name``: Preferred display name (hierarchy: ``nome_usual`` > ``nome_social`` > ``nome_registro`` > ``user.username``).
- ``campus_sigla``: Campus acronym (e.g. ``"CNAT"``) or empty string.
- ``foto_url``: Profile picture URL (prioritizes 150x200 over 75x100).
- ``theme_selected``: Theme selected in ``settings`` (default: ``"ifrn25"``).
- ``menu_position``: Menu position defined in ``settings`` (default: ``"bottom"``).
- ``color_mode``: Accessibility color mode (default: ``"default"``).
- ``zoom_level``: Accessibility zoom level as integer (default: ``100``).
- Accessibility properties (booleans from ``settings``): ``dyslexia_friendly``, ``remove_justify``, ``highlight_links``, ``stop_animations``, ``hidden_illustrative_image``, ``big_cursor``, ``vlibras_active`` (default `True`), ``high_line_height``.

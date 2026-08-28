==========
What's New
==========

This page summarizes the new features and improvements introduced in the **1.8.x** series of ``django-suap-auth``.

.. note::
   This page must be updated with every new release published.

Version 1.8.4
=============

- **Dutch Internationalization (``nl``)**: Added code internationalization support for Dutch (translation catalogs ``.po``/``.mo`` for ``nl``).

Version 1.8.3
=============

- **Audit Alert Settings**: Externalized security alert thresholds to ``settings.py`` via ``SUAP_AUTH_AUDIT_*`` configuration settings.

Version 1.8.2
=============

- **Django Admin Shortcut**: Added a direct shortcut button to the Audit Dashboard from the Django Admin Audit Events change list.

Version 1.8.1
=============

- **Resilience & Migration**: Added fault-tolerant error handling to audit logging and updated sandbox migrations.

Version 1.8.0
=============

- **New Audit Module (``django_suap_auth.audit``)**:
  - Audit logging trail capturing authentication events, token exchanges, and user accesses.
  - Interactive dashboard integrated into Django Admin.
  - Security signals and monitoring support.

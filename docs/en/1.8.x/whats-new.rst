==========
What's New
==========

This page summarizes the new features and improvements introduced in the **1.8.x** series of ``django-suap-auth``.

.. note::
   This page must be updated with every new release published.

Version 1.8.9
=============

- **Access-Denied Page for Authenticated User Without Permission**: ``SuapLoginView`` now detects when it is hit by an already-authenticated user (a sign that a permission check elsewhere failed, such as Django Admin's ``has_permission``) and, instead of restarting the OAuth2 flow — creating a confusing login loop —, renders a page explaining that the user is logged in but lacks permission for the requested resource. Customizable via the ``access_denied_template`` attribute.

Version 1.8.8
=============

- **Sentry Notification Level Set to ``info`` for Secondary Sync Failures**: Notifications sent to Sentry when fetching secondary SUAP user info endpoints now use severity level ``info`` instead of ``error``, avoiding error/bug alerts for non-critical failures that do not block user login.

Version 1.8.7
=============

- **Prioritized Persistence of DadosBrutos**: Updated the profile sync workflow (`sync_suap_profile`) to save the `DadosBrutos` raw data model before attempting to build or save `Perfil` and `Vinculo` models, guaranteeing raw SUAP data is persisted even if profile save fails.

Version 1.8.6
=============

- **Profile and Audit Model Field Length Expansion**: Increased ``max_length`` of profile, audit, and error model fields (from 10/50/100 to 256) to prevent ``DataError`` failures when receiving longer text values from SUAP API endpoints (e.g. gender "PREFERE NÃO INFORMAR", blood type "NÃO INFORMADO").
- **Sentry Error Filtering for HTTP 404 and 403**: Updated ``report_sync_error_to_sentry`` service to ignore HTTP 404 (Not Found) and 403 (Forbidden) statuses during secondary fetcher requests, avoiding false error alerts in Sentry when optional endpoints have no data for specific users.

Version 1.8.5
=============

- **Error Handling in Secondary Fetchers**: Fixed fault tolerance when retrieving user profile data via fetchers and SUAP API endpoints. Errors on secondary endpoints now record sync errors in ``_sync_errors`` and allow login to complete, interrupting authentication only if the failure occurs on the primary identification endpoint (``/api/rh/eu/``).

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

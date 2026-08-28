===============================
Audit Trail and Admin Dashboard
===============================

The ``django_suap_auth.audit`` sub-module provides a centralized audit trail and dashboard compliant with LGPD and security standards.

Key Features
============

* **Authentication and Impersonate Events**: Automatic recording of SUAP logins (success/failure), JWT issuance/refresh, and impersonate sessions.
* **API Integration (Django Ninja / DRF)**: Endpoint access capture with execution duration (``duration_ms``) and HTTP status codes.
* **Correlation ID**: Automatic injection of the ``X-Correlation-ID`` header for request flow tracing.
* **LGPD Governance**: Raw IP storage restricted by permission (``django_suap_auth_audit.view_raw_ip``) and SHA-256 IP hashing for analytics.
* **5-Year Retention**: Cold storage compressed archiving support via ``python manage.py audit_archive``.
* **Django Admin Dashboard**: Native visual dashboard supporting Light Mode and Dark Mode.
* **Automated Alerts**: Anomaly detection rules with notifications via Admin, Email, Webhook, and Telegram.

Configuration
=============

Add ``django_suap_auth.audit`` to ``INSTALLED_APPS`` and configure middleware:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "django_suap_auth",
        "django_suap_auth.audit",
    ]

    MIDDLEWARE = [
        "django_suap_auth.audit.middleware.CorrelationMiddleware",
        "django_suap_auth.audit.middleware.AuditMiddleware",
        # ...
    ]

Archiving Command
=================

To archive audit records older than 365 days:

.. code-block:: bash

    python manage.py audit_archive --days=365 --output=/path/to/backup.jsonl.gz

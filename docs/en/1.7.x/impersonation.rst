==================
User Impersonation
==================

The ``django_suap_auth.impersonation`` sub-app provides user impersonation features, allowing superusers to simulate other user sessions during support and testing workflows.

Installation
============

Add ``django_suap_auth.impersonation`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "django_suap_auth",
        "django_suap_auth.impersonation",
    ]

Routes and Views
================

Include impersonation URLs in your project's ``urls.py``:

.. code-block:: python

    from django.urls import include, path

    urlpatterns = [
        path("auth/impersonation/", include("django_suap_auth.impersonation.urls")),
    ]

Available views:

- ``ImpersonateView`` (route ``impersonate/<str:username>/`` or ``impersonate/`` with query/POST parameter):
  Starts user impersonation. Restricted to superusers and prevents impersonating other superusers or nested impersonations.
- ``StopImpersonatingView`` (route ``stop-impersonating/``):
  Ends active impersonation for the session.

Helpers
=======

The sub-app provides utility functions:

.. code-block:: python

    from django_suap_auth.impersonation.helpers import get_active_user, is_impersonating

    # Returns impersonated User instance if an impersonation session is active;
    # otherwise returns request.user.
    user = get_active_user(request)

    # Returns True if the current request is an active impersonation session.
    impersonating = is_impersonating(request)

Context Processor
=================

To include impersonation context variables in templates, add the context processor in ``settings.py``:

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "context_processors": [
                    # ...
                    "django_suap_auth.impersonation.context_processors.impersonation",
                ],
            },
        },
    ]

Template context variables:

- ``active_user``: The active user instance (considering impersonation).
- ``is_impersonating``: Boolean indicating if impersonation is active.

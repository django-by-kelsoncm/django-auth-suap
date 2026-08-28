from django.apps import AppConfig


class SuapAuthAuditConfig(AppConfig):
    name = "django_suap_auth.audit"
    label = "django_suap_auth_audit"
    verbose_name = "SUAP Auth Auditoria"

    def ready(self):
        from . import receivers  # noqa: F401

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SuapAuthImpersonationConfig(AppConfig):
    name = "django_suap_auth.impersonation"
    label = "django_suap_auth_impersonation"
    verbose_name = _("SUAP Auth Impersonation")

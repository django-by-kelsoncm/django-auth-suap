from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SuapAuthErrosConfig(AppConfig):
    name = "django_suap_auth.erros"
    label = "django_suap_auth_erros"
    verbose_name = _("SUAP Auth Erros")

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SuapAuthProfileConfig(AppConfig):
    name = "django_suap_auth.profile"
    label = "django_suap_auth_profile"
    verbose_name = _("SUAP Auth Profile")

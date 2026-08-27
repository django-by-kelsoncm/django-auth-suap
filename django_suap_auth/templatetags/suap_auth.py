from django import template

from django_suap_auth.utils import get_suap_settings

register = template.Library()


@register.simple_tag
def suap_base_url():
    """Return the configured SUAP base URL without trailing slash."""
    cfg = get_suap_settings(require_oauth=False)
    return cfg.get("base_url", "https://suap.ifrn.edu.br").rstrip("/")


@register.simple_tag
def suap_login_url():
    """Return the SUAP login/logout accounts page URL."""
    base_url = suap_base_url()
    return f"{base_url}/accounts/login/"

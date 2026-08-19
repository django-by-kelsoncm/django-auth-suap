import secrets

from django.core.exceptions import ImproperlyConfigured

# Default mapping: user model field → SUAP response key.
DEFAULT_USER_ATTR_MAP = {
    "username": "identificacao",
    "email": "email",
    ("first_name", "last_name"): "nome_registro",
}

DEFAULT_USER_INFO_ENDPOINTS = [
    "/api/rh/eu/",
]


def get_suap_settings(require_oauth=True):
    """Read and validate SUAP settings from Django settings.

    Expects a single SUAP_AUTH dictionary with all configuration:

    SUAP_AUTH = {
        'CLIENT_ID': 'your-id',
        'CLIENT_SECRET': 'your-secret',
        'REDIRECT_URI': 'https://example.com/callback/',
        'BASE_URL': 'https://suap.ifrn.edu.br',  # optional
        'SCOPES': ['identificacao', 'email'],  # optional
        'USER_LOOKUP_FIELD': 'username',  # optional
        'USER_ATTR_MAP': {...},  # optional
        'USER_INFO_FETCHERS': [...],  # optional Chain of Responsibility
        'USER_INFO_ENDPOINTS': [...],  # optional endpoints
        'USER_INFO_MAPPERS': [...],  # optional Chain of Responsibility
        'USER_JSON_FIELD': None,  # optional
        'DIRECT_REDIRECT': True,  # optional
    }
    """
    from django.conf import settings

    suap_auth = getattr(settings, "SUAP_AUTH", {})

    if require_oauth:
        # Validate required fields
        required = ["CLIENT_ID", "CLIENT_SECRET", "REDIRECT_URI"]
        missing = [field for field in required if not suap_auth.get(field)]

        if missing:
            raise ImproperlyConfigured(
                f"Missing required SUAP_AUTH settings: {', '.join(missing)}. "
                f"Configure SUAP_AUTH dictionary in settings.py"
            )

    # Legacy USER_MAPPER compatibility
    default_mappers = ["django_suap_auth.mappers.DefaultAttrMapUserMapper"]
    if "USER_MAPPER" in suap_auth:
        default_mappers = [suap_auth["USER_MAPPER"]]

    return {
        "client_id": suap_auth.get("CLIENT_ID", ""),
        "client_secret": suap_auth.get("CLIENT_SECRET", ""),
        "redirect_uri": suap_auth.get("REDIRECT_URI", ""),
        "scopes": suap_auth.get("SCOPES", ["identificacao", "email"]),
        "base_url": suap_auth.get("BASE_URL", "https://suap.ifrn.edu.br"),
        "user_lookup_field": suap_auth.get("USER_LOOKUP_FIELD", "username"),
        "user_attr_map": suap_auth.get("USER_ATTR_MAP", DEFAULT_USER_ATTR_MAP),
        "user_info_fetchers": suap_auth.get(
            "USER_INFO_FETCHERS", ["django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher"]
        ),
        "user_info_endpoints": suap_auth.get("USER_INFO_ENDPOINTS", DEFAULT_USER_INFO_ENDPOINTS),
        "user_info_mappers": suap_auth.get("USER_INFO_MAPPERS", default_mappers),
        "json_field": suap_auth.get("USER_JSON_FIELD", None),
        "direct_redirect": suap_auth.get("DIRECT_REDIRECT", True),
        "backend": suap_auth.get("BACKEND", "django_suap_auth.backends.SuapAuthBackend"),
        "create_user": suap_auth.get("CREATE_USER", True),
        "user_defaults": suap_auth.get("USER_DEFAULTS", {"is_active": True}),
        "first_user_defaults": suap_auth.get("FIRST_USER_DEFAULTS", {"is_staff": True, "is_superuser": True}),
        "update_fields_on_create": suap_auth.get("UPDATE_FIELDS_ON_CREATE", None),
        "update_fields_on_login": suap_auth.get("UPDATE_FIELDS_ON_LOGIN", None),
    }


def _extract_nested(data, dotted_key):
    """Extract a value from a (possibly nested) dict using a dotted key path."""
    from .mappers import _extract_nested as mapper_extract

    return mapper_extract(data, dotted_key)


def get_user_mapper(cfg=None):
    """Instantiate and return the configured SUAP user mapper chain or first mapper."""
    from .mappers import get_user_info_mappers

    mappers = get_user_info_mappers(cfg)
    return mappers[0] if mappers else None


def apply_user_attr_map(user_info, attr_map, cfg=None):
    """Translate a SUAP user_info dict into a flat dict of user model field→value pairs.

    Executes the configured USER_INFO_MAPPERS Chain of Responsibility.
    """
    from .mappers import run_user_info_mapper_chain

    return run_user_info_mapper_chain(user_info, attr_map, cfg=cfg)


def get_oauth2_client(require_oauth=True):
    """Return a SuapOAuth2Client configured from Django settings."""
    from .client import SuapOAuth2Client

    cfg = get_suap_settings(require_oauth=require_oauth)
    return SuapOAuth2Client(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_uri=cfg["redirect_uri"],
        scopes=cfg["scopes"],
        base_url=cfg["base_url"],
    )


def generate_state():
    """Generate a cryptographically secure random state token for OAuth2 CSRF protection."""
    return secrets.token_urlsafe(32)

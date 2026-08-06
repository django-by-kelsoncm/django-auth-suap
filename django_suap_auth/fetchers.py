import inspect
import logging

from django.utils.module_loading import import_string

from .exceptions import SuapUserInfoError

logger = logging.getLogger(__name__)

DEFAULT_SUAP_ENDPOINTS = [
    "/api/rh/eu/",
]


def resolve_callable_or_class(target):
    """Resolve a callable, class, or python import path string."""
    if callable(target):
        return target
    if isinstance(target, str):
        return import_string(target)
    raise TypeError(f"Expected callable, class, or import path string, got {type(target)}")


def resolve_callable(target):
    """Resolve a callable, class, or import path string (backward compatible name)."""
    return resolve_callable_or_class(target)


class BaseUserInfoFetcher:
    """Base class for User Info Fetchers in the Chain of Responsibility."""

    def __init__(self, suap_settings=None):
        self.suap_settings = suap_settings or {}

    def fetch(self, client, access_token, user_info=None):
        if user_info is None:
            user_info = {}
        return user_info


class DefaultEndpointsUserInfoFetcher(BaseUserInfoFetcher):
    """Fetcher link that iterates over SUAP_AUTH['USER_INFO_ENDPOINTS'] and merges profile data."""

    def fetch(self, client, access_token, user_info=None):
        if user_info is None:
            user_info = {}

        endpoints = self.suap_settings.get("user_info_endpoints", DEFAULT_SUAP_ENDPOINTS)

        for endpoint_spec in endpoints:
            try:
                if isinstance(endpoint_spec, str):
                    url_path = endpoint_spec
                    if "{" in url_path and "}" in url_path:
                        try:
                            url_path = url_path.format(**user_info)
                        except KeyError as exc:
                            logger.warning("Could not format SUAP endpoint '%s' with user_info: %s", url_path, exc)
                            continue
                    data = client.get_endpoint_data(access_token, url_path)
                    if isinstance(data, dict):
                        user_info.update(data)

                elif isinstance(endpoint_spec, dict):
                    url_path = endpoint_spec.get("endpoint")
                    namespace = endpoint_spec.get("namespace")
                    extract_list = endpoint_spec.get("extract_list")
                    for_each = endpoint_spec.get("for_each")

                    if not url_path:
                        continue

                    if for_each:
                        items = user_info.get(for_each, [])
                        if isinstance(items, list):
                            aggregated = []
                            for item in items:
                                if isinstance(item, dict):
                                    ctx = dict(user_info)
                                    ctx.update(item)
                                    try:
                                        formatted_url = url_path.format(**ctx)
                                    except KeyError as exc:
                                        logger.warning("Could not format SUAP endpoint '%s' with item %s: %s", url_path, item, exc)
                                        continue
                                    try:
                                        data = client.get_endpoint_data(access_token, formatted_url)
                                        if extract_list and isinstance(data, dict):
                                            extracted = data.get(extract_list, [])
                                        else:
                                            extracted = data

                                        if isinstance(extracted, list):
                                            aggregated.extend(extracted)
                                        elif isinstance(extracted, dict):
                                            aggregated.append(extracted)
                                    except Exception as exc:
                                        logger.warning("Failed to fetch SUAP user info endpoint '%s': %s", formatted_url, exc)
                            if namespace:
                                user_info[namespace] = aggregated
                        continue

                    if "{" in url_path and "}" in url_path:
                        try:
                            url_path = url_path.format(**user_info)
                        except KeyError as exc:
                            logger.warning("Could not format SUAP endpoint '%s' with user_info: %s", url_path, exc)
                            continue

                    data = client.get_endpoint_data(access_token, url_path)

                    if extract_list and isinstance(data, dict):
                        data_to_store = data.get(extract_list, [])
                    else:
                        data_to_store = data

                    if namespace:
                        user_info[namespace] = data_to_store
                    elif isinstance(data_to_store, dict):
                        user_info.update(data_to_store)
            except Exception as exc:
                if isinstance(exc, SuapUserInfoError):
                    raise
                logger.warning("Failed to fetch SUAP user info endpoint '%s': %s", endpoint_spec, exc)

        return user_info


def get_user_info_fetchers(cfg=None):
    """Instantiate and return the list of fetchers in the Chain of Responsibility."""
    from .utils import get_suap_settings

    if cfg is None:
        cfg = get_suap_settings()

    fetcher_targets = cfg.get("user_info_fetchers", ["django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher"])
    fetchers = []

    for target in fetcher_targets:
        cls = resolve_callable_or_class(target)
        if inspect.isclass(cls):
            fetchers.append(cls(suap_settings=cfg))
        elif callable(cls):
            fetchers.append(cls)

    return fetchers


def run_user_info_fetcher_chain(client, access_token, cfg=None):
    """Execute the Chain of Responsibility for fetching user profile info."""
    fetchers = get_user_info_fetchers(cfg)
    user_info = {}

    for fetcher in fetchers:
        if hasattr(fetcher, "fetch"):
            user_info = fetcher.fetch(client, access_token, user_info)
        elif callable(fetcher):
            user_info = fetcher(client, access_token, user_info)

    return user_info

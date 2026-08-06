import inspect

from django.utils.module_loading import import_string


def _extract_nested(data, dotted_key):
    """Extract a value from a (possibly nested) dict using a dotted key path."""
    if not dotted_key or not isinstance(dotted_key, str):
        return None
    keys = dotted_key.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None
    return value


def resolve_callable_or_class(target):
    """Resolve a callable, class, or python import path string."""
    if callable(target):
        return target
    if isinstance(target, str):
        return import_string(target)
    raise TypeError(f"Expected callable, class, or import path string, got {type(target)}")


def _call_transformer(fn, raw_val, user_info):
    """Call a transformer function trying flexible argument signatures."""
    sig = inspect.signature(fn)
    param_count = len(sig.parameters)

    if param_count == 1:
        return fn(raw_val)
    elif param_count == 2:
        return fn(raw_val, user_info)
    else:
        try:
            return fn(raw_val, user_info)
        except TypeError:
            return fn(raw_val)


class BaseUserMapper:
    """Base class for User Info Mappers in the Chain of Responsibility."""

    def __init__(self, suap_settings=None):
        self.suap_settings = suap_settings or {}

    def map_attributes(self, user_info, attrs=None):
        if attrs is None:
            attrs = {}
        return attrs


class DefaultAttrMapUserMapper(BaseUserMapper):
    """Default User Info Mapper link applying SUAP_AUTH['USER_ATTR_MAP']."""

    def map_attributes(self, user_info, attrs=None):
        if attrs is None:
            attrs = {}

        attr_map = self.suap_settings.get("user_attr_map", {})

        for model_field, spec in attr_map.items():
            if callable(spec):
                val = _call_transformer(spec, user_info, user_info)
                if val is not None:
                    attrs[model_field] = val
                continue

            if isinstance(spec, str):
                if spec == "fulljson":
                    attrs[model_field] = user_info
                    continue
                val = _extract_nested(user_info, spec)
                if val is None:
                    continue
                if isinstance(model_field, (list, tuple)) and len(model_field) == 2:
                    field_a, field_b = model_field
                    parts = str(val).split(" ", 1)
                    attrs[field_a] = parts[0]
                    attrs[field_b] = parts[1] if len(parts) > 1 else ""
                else:
                    attrs[model_field] = val
                continue

            if isinstance(spec, dict):
                key = spec.get("key")
                default_val = spec.get("default")
                transform = spec.get("transform")

                raw_val = _extract_nested(user_info, key) if key else None
                if raw_val is None:
                    raw_val = default_val

                if raw_val is None and not transform:
                    continue

                if transform:
                    transform_fn = resolve_callable_or_class(transform)
                    val = _call_transformer(transform_fn, raw_val, user_info)
                else:
                    val = raw_val

                if val is not None:
                    attrs[model_field] = val
                continue

        return attrs


# Alias for backward compatibility
BaseSuapUserMapper = BaseUserMapper
DefaultSuapUserMapper = DefaultAttrMapUserMapper


def get_user_info_mappers(cfg=None):
    """Instantiate and return the list of mappers in the Chain of Responsibility."""
    from .utils import get_suap_settings

    if cfg is None:
        cfg = get_suap_settings()

    mapper_targets = cfg.get("user_info_mappers", ["django_suap_auth.mappers.DefaultAttrMapUserMapper"])
    mappers = []

    for target in mapper_targets:
        cls = resolve_callable_or_class(target)
        if inspect.isclass(cls):
            mappers.append(cls(suap_settings=cfg))
        elif callable(cls):
            mappers.append(cls)

    return mappers


def run_user_info_mapper_chain(user_info, attr_map=None, cfg=None):
    """Execute the Chain of Responsibility for mapping user_info to model field attributes."""
    mappers = get_user_info_mappers(cfg)
    attrs = {}

    for mapper in mappers:
        if hasattr(mapper, "map_attributes"):
            attrs = mapper.map_attributes(user_info, attrs)
        elif callable(mapper):
            attrs = mapper(user_info, attrs)

    return attrs

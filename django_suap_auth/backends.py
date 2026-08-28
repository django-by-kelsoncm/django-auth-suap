from django.contrib.auth import get_user_model

from .exceptions import SuapUserNotAllowedError
from .utils import apply_user_attr_map, get_suap_settings


def _filter_fields(attrs, allowed):
    """Return a subset of *attrs* restricted to *allowed* field names.

    ``allowed=None`` means no restriction (return all fields).
    ``allowed=[]`` means return an empty dict.
    """
    if allowed is None:
        return dict(attrs)
    return {k: v for k, v in attrs.items() if k in allowed}


class SuapAuthBackend:
    """
    Django authentication backend for SUAP OAuth2.

    Looks up or creates a Django user based on the profile info returned by SUAP.

    Behaviour is controlled by ``SUAP_AUTH`` settings:

    * ``CREATE_USER`` (bool, default ``True``) — when ``False``, raises
      :exc:`~django_suap_auth.exceptions.SuapUserNotAllowedError` for users
      that do not yet have a local account.
    * ``USER_DEFAULTS`` (dict, default ``{"is_active": True}``) — extra
      field values applied only when creating a new user.
    * ``UPDATE_FIELDS_ON_CREATE`` (list or ``None``, default ``None``) —
      mapped fields written when a new user is created.  ``None`` means all
      mapped fields; ``[]`` means none.
    * ``UPDATE_FIELDS_ON_LOGIN`` (list or ``None``, default ``None``) —
      mapped fields synced on every subsequent login.  ``None`` means all
      mapped fields; ``[]`` means none.
    * ``FIRST_USER_DEFAULTS`` (dict or ``None``, default ``None``) — when set,
      these field values are used instead of ``USER_DEFAULTS`` if no users
      exist yet (e.g. ``{"is_superuser": True, "is_staff": True}``).

    Override individual methods to customise behaviour without rewriting
    ``authenticate`` entirely:

    * :meth:`get_user_attrs` — map raw SUAP info to model field dict.
    * :meth:`get_lookup_value` — extract the lookup key from mapped attrs.
    * :meth:`get_or_create_user` — fetch or create the local user.
    * :meth:`create_user` — instantiate and save a brand-new user.
    * :meth:`update_user` — sync fields on an existing user.
    """

    def authenticate(self, request, suap_user_info=None, **kwargs):
        if suap_user_info is None:
            return None

        cfg = get_suap_settings()
        lookup_field = cfg["user_lookup_field"]

        attrs = self.get_user_attrs(suap_user_info, cfg)
        lookup_value = self.get_lookup_value(attrs, lookup_field)
        if not lookup_value:
            return None

        mapped_attrs = {k: v for k, v in attrs.items() if k != lookup_field}
        try:
            user = self.get_or_create_user(lookup_field, lookup_value, mapped_attrs, cfg)
        except Exception as exc:
            from .audit.signals import suap_auth_failed

            suap_auth_failed.send(sender=self.__class__, request=request, reason=str(exc))
            raise exc

        if user is not None:
            if "_sync_errors" in suap_user_info:
                from .erros.services import save_sync_errors_for_user

                save_sync_errors_for_user(user, suap_user_info["_sync_errors"])
            from .audit.signals import suap_auth_success

            suap_auth_success.send(sender=self.__class__, request=request, user=user, suap_user_info=suap_user_info)

        return user

    # ------------------------------------------------------------------
    # Extension points
    # ------------------------------------------------------------------

    def get_user_attrs(self, suap_user_info, cfg):
        """Return a dict of model-field → value built from *suap_user_info*.

        Override to add, remove, or transform attributes before the user is
        looked up or created.
        """
        attrs = apply_user_attr_map(suap_user_info, cfg["user_attr_map"], cfg=cfg)
        if cfg["json_field"]:
            attrs[cfg["json_field"]] = suap_user_info
        return attrs

    def get_lookup_value(self, attrs, lookup_field):
        """Return the value used to look up the local user record.

        Return ``None`` to abort authentication (backend returns ``None``).
        """
        return attrs.get(lookup_field)

    def get_or_create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
        """Fetch the existing user or create a new one.

        Raises :exc:`~django_suap_auth.exceptions.SuapUserNotAllowedError`
        when the user does not exist and ``CREATE_USER`` is ``False``.
        """
        User = get_user_model()
        try:
            user = User.objects.get(**{lookup_field: lookup_value})
        except User.DoesNotExist:
            if not cfg["create_user"]:
                raise SuapUserNotAllowedError(
                    f"No local account for SUAP user '{lookup_value}' and CREATE_USER is disabled."
                )
            return self.create_user(lookup_field, lookup_value, mapped_attrs, cfg)

        return self.update_user(user, mapped_attrs, cfg)

    def create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
        """Instantiate, populate, and save a brand-new local user.

        When ``FIRST_USER_DEFAULTS`` is configured and no users exist yet, those
        defaults are used instead of ``USER_DEFAULTS``.

        Override to hook into the creation process (e.g. send a welcome e-mail,
        assign groups, etc.).
        """
        User = get_user_model()
        defaults = dict(cfg["user_defaults"])
        first_defaults = cfg["first_user_defaults"]
        if first_defaults is not None and not User.objects.exists():
            defaults.update(first_defaults)
        defaults.update(_filter_fields(mapped_attrs, cfg["update_fields_on_create"]))

        user_fields = {f.name for f in User._meta.get_fields()}
        user_kwargs = {k: v for k, v in defaults.items() if k in user_fields or hasattr(User, k)}
        user_kwargs[lookup_field] = lookup_value

        user = User(**user_kwargs)
        user.save()
        return user

    def update_user(self, user, mapped_attrs, cfg):
        """Sync *mapped_attrs* onto an existing *user* and save if changed.

        Override to add custom logic on every login (e.g. update group
        membership based on SUAP roles).
        """
        changed = False

        for field, value in _filter_fields(mapped_attrs, cfg["update_fields_on_login"]).items():
            if hasattr(user, field):
                if getattr(user, field, None) != value:
                    setattr(user, field, value)
                    changed = True

        # Always enforce user_defaults (e.g. reactivate a deactivated account)
        for field, value in cfg["user_defaults"].items():
            if hasattr(user, field):
                if getattr(user, field, None) != value:
                    setattr(user, field, value)
                    changed = True

        if changed:
            user.save()

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

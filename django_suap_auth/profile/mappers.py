from django_suap_auth.mappers import BaseUserMapper

from .backends import sync_suap_profile


class ProfileModelUserMapper(BaseUserMapper):
    """User Info Mapper that triggers Perfil, DadosBrutos, and Vinculo model synchronization."""

    def map_attributes(self, user_info, attr_map=None):
        attrs = super().map_attributes(user_info, attr_map)
        user = user_info.get("_user")
        if user:
            sync_suap_profile(user, user_info)
        return attrs

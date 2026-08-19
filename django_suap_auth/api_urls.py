from django.urls import re_path

from .jwt_views import SuapTokenPairView, SuapTokenRefreshView, SuapTokenVerifyView, SuapUserInfoFetchView

app_name = "suap_api"

urlpatterns = [
    re_path(r"^api/token/pair/?$", SuapTokenPairView.as_view(), name="token_pair"),
    re_path(r"^api/token/refresh/?$", SuapTokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"^api/token/verify/?$", SuapTokenVerifyView.as_view(), name="token_verify"),
    re_path(r"^api/token/user-info/?$", SuapUserInfoFetchView.as_view(), name="token_user_info"),
    re_path(r"^api/rh/eu/?$", SuapUserInfoFetchView.as_view(), name="rh_eu"),
]

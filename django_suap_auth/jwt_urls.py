from django.urls import re_path

from .jwt_views import SuapTokenPairView, SuapTokenRefreshView, SuapTokenVerifyView

app_name = "suap_jwt"

urlpatterns = [
    re_path(r"^pair/?$", SuapTokenPairView.as_view(), name="pair"),
    re_path(r"^refresh/?$", SuapTokenRefreshView.as_view(), name="refresh"),
    re_path(r"^verify/?$", SuapTokenVerifyView.as_view(), name="verify"),
]

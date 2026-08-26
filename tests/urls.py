from django.urls import include, path

urlpatterns = [
    path("auth/suap/", include("django_suap_auth.urls")),
    path("api/token/", include("django_suap_auth.jwt.urls")),
    path("token/", include("django_suap_auth.token_urls")),
    path("", include("django_suap_auth.api_urls")),
]

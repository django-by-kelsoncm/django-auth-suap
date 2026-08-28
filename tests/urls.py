from django.http import HttpResponse
from django.urls import include, path


def dummy_view(request):
    return HttpResponse("OK")


urlpatterns = [
    path("dashboard/", dummy_view, name="dashboard"),
    path("profile/", dummy_view, name="profile"),
    path("home/", dummy_view, name="home"),
    path("auth/suap/", include("django_suap_auth.urls")),
    path("auth/impersonation/", include("django_suap_auth.impersonation.urls")),
    path("api/token/", include("django_suap_auth.jwt.urls")),
    path("token/", include("django_suap_auth.token_urls")),
    path("", include("django_suap_auth.api_urls")),
]

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/suap/", include("django_suap_auth.urls")),
    path("api/token/", include("django_suap_auth.jwt_urls")),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", include("home.urls")),
]

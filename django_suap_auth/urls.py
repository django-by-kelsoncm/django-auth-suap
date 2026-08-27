from django.urls import path

from .views import SuapCallbackView, SuapLoginView, SuapLogoutView

app_name = "suap_auth"

urlpatterns = [
    path("login/", SuapLoginView.as_view(), name="login"),
    path("callback/", SuapCallbackView.as_view(), name="callback"),
    path("logout/", SuapLogoutView.as_view(), name="logout"),
]

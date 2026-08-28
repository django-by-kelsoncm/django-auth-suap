from django.urls import path

from .views import ImpersonateView, StopImpersonatingView

app_name = "suap_auth_impersonation"

urlpatterns = [
    path("impersonate/", ImpersonateView.as_view(), name="impersonate_param"),
    path("impersonate/<str:username>/", ImpersonateView.as_view(), name="impersonate"),
    path("stop-impersonating/", StopImpersonatingView.as_view(), name="stop_impersonating"),
]

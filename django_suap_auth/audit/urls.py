from django.urls import path

from .views import AuditDashboardView

app_name = "django_suap_auth_audit"

urlpatterns = [
    path("dashboard/", AuditDashboardView.as_view(), name="dashboard"),
]

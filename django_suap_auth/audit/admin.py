from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import AuditEvent, EventSeverity
from .views import AuditDashboardView


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    change_list_template = "admin/django_suap_auth/audit/auditevent/change_list.html"
    list_display = [
        "timestamp_format",
        "event_type",
        "category",
        "severity_badge",
        "user_identifier",
        "impersonator_identifier",
        "display_ip",
        "status_code",
        "duration_ms",
    ]
    list_filter = ["category", "severity", "application_name", "status_code", "timestamp"]
    search_fields = [
        "correlation_id",
        "user_identifier",
        "impersonator_identifier",
        "ip_address",
        "ip_hashed",
        "request_path",
    ]
    readonly_fields = [field.name for field in AuditEvent._meta.fields] + ["ip_hashed"]
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Data / Hora"), ordering="timestamp")
    def timestamp_format(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @admin.display(description=_("Gravidade"), ordering="severity")
    def severity_badge(self, obj):
        colors = {
            EventSeverity.INFO: "var(--accent, #417690)",
            EventSeverity.WARNING: "var(--warning-fg, #b45d00)",
            EventSeverity.CRITICAL: "#dc3545",
        }
        color = colors.get(obj.severity, "var(--body-fg)")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_severity_display())

    @admin.display(description=_("Endereço IP"))
    def display_ip(self, obj):
        # Verifica se o usuário possui a permissão restrita para ver o IP bruto
        if self.current_request and self.current_request.user.has_perm("django_suap_auth_audit.view_raw_ip"):
            return obj.ip_address or "-"
        return obj.ip_hashed[:12] + "..." if obj.ip_hashed else "-"

    def get_queryset(self, request):
        self.current_request = request
        return super().get_queryset(request)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "dashboard/",
                self.admin_site.admin_view(AuditDashboardView.as_view()),
                name="django_suap_auth_audit_dashboard",
            ),
        ]
        return custom_urls + urls

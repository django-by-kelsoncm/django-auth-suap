from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from .models import AuditEvent, EventCategory


@method_decorator(staff_member_required, name="dispatch")
class AuditDashboardView(View):
    """View do Dashboard de Auditoria integrado ao Django Admin com suporte nativo a Tema Claro/Escuro."""

    template_name = "admin/django_suap_auth/audit/dashboard.html"

    def get(self, request, *args, **kwargs):
        period = request.GET.get("period", "7d")
        now = timezone.now()

        if period == "24h":
            start_date = now - timedelta(hours=24)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)

        events_qs = AuditEvent.objects.filter(timestamp__gte=start_date)

        # KPIs Principais
        total_events = events_qs.count()

        auth_success_count = events_qs.filter(event_type="auth.login.success").count()
        auth_failed_count = events_qs.filter(event_type="auth.login.failed").count()
        total_logins = auth_success_count + auth_failed_count
        success_rate = round((auth_success_count / total_logins) * 100, 1) if total_logins > 0 else 100.0

        impersonate_count = events_qs.filter(category=EventCategory.IMPERSONATION).count()
        api_count = events_qs.filter(category=EventCategory.API_ACCESS).count()
        security_alerts_count = events_qs.filter(category=EventCategory.SECURITY_ALERT).count()

        # Agregação Temporal para Gráfico de Séries Temporais
        daily_stats = (
            events_qs.annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(
                total=Count("id"),
                logins=Count("id", filter=Q(event_type="auth.login.success")),
                login_failures=Count("id", filter=Q(event_type="auth.login.failed")),
                api_calls=Count("id", filter=Q(category=EventCategory.API_ACCESS)),
                impersonates=Count("id", filter=Q(category=EventCategory.IMPERSONATION)),
            )
            .order_by("date")
        )

        chart_labels = [item["date"].strftime("%d/%m/%Y") for item in daily_stats if item["date"]]
        chart_logins = [item["logins"] for item in daily_stats]
        chart_api = [item["api_calls"] for item in daily_stats]
        chart_impersonates = [item["impersonates"] for item in daily_stats]

        # Top 5 Superusuários em Impersonate
        top_impersonators = (
            events_qs.filter(category=EventCategory.IMPERSONATION)
            .exclude(impersonator_identifier="")
            .values("impersonator_identifier")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        # Top 5 Endpoints Ninja / API mais acessados
        top_endpoints = (
            events_qs.filter(category=EventCategory.API_ACCESS)
            .exclude(request_path="")
            .values("request_path")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        # Últimos Alertas de Segurança
        recent_alerts = events_qs.filter(category=EventCategory.SECURITY_ALERT).order_by("-timestamp")[:10]

        context = {
            "title": "Dashboard de Auditoria & Segurança SUAP",
            "subtitle": f"Análise temporal consolidades - Período: {period}",
            "period": period,
            "total_events": total_events,
            "total_logins": total_logins,
            "auth_success_count": auth_success_count,
            "auth_failed_count": auth_failed_count,
            "success_rate": success_rate,
            "impersonate_count": impersonate_count,
            "api_count": api_count,
            "security_alerts_count": security_alerts_count,
            "chart_labels": chart_labels,
            "chart_logins": chart_logins,
            "chart_api": chart_api,
            "chart_impersonates": chart_impersonates,
            "top_impersonators": top_impersonators,
            "top_endpoints": top_endpoints,
            "recent_alerts": recent_alerts,
            "has_permission": True,
            "site_header": getattr(request, "site_header", "Administração Django"),
            "site_title": "Auditoria SUAP",
        }

        return render(request, self.template_name, context)

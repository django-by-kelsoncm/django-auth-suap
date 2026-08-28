import time
import uuid

from django.utils.deprecation import MiddlewareMixin

from .models import EventCategory, EventSeverity
from .services import record_audit_event


class CorrelationMiddleware(MiddlewareMixin):
    """Middleware que garante que toda requisição HTTP possua um X-Correlation-ID único."""

    def process_request(self, request):
        correlation_id = (
            request.headers.get("X-Correlation-ID") or request.META.get("HTTP_X_CORRELATION_ID") or str(uuid.uuid4())
        )
        request.correlation_id = correlation_id

    def process_response(self, request, response):
        if hasattr(request, "correlation_id"):
            response["X-Correlation-ID"] = request.correlation_id
        return response


class AuditMiddleware(MiddlewareMixin):
    """Middleware que intercepta chamadas a endpoints e APIs, medindo tempo de execução e auditando acessos."""

    def process_request(self, request):
        request._audit_start_time = time.time()

    def process_response(self, request, response):
        # Ignora arquivos estáticos e favicon
        path = request.path
        if path.startswith("/static/") or path.startswith("/media/") or path == "/favicon.ico":
            return response

        start_time = getattr(request, "_audit_start_time", time.time())
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Trata gravidade baseada no status code
        severity = EventSeverity.INFO
        if response.status_code in [401, 403]:
            severity = EventSeverity.WARNING
        elif response.status_code >= 500:
            severity = EventSeverity.CRITICAL

        # Se for endpoint de API (ex: Django Ninja v1/v2 ou DRF) ou alteração relevante (POST/PUT/DELETE)
        is_api_path = path.startswith("/api/") or "/api/" in path
        if is_api_path or request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            category = EventCategory.API_ACCESS if is_api_path else EventCategory.AUTHENTICATION
            event_type = "api.ninja.access" if is_api_path else f"http.{request.method.lower()}"

            record_audit_event(
                category=category,
                event_type=event_type,
                severity=severity,
                request=request,
                status_code=response.status_code,
                duration_ms=duration_ms,
                metadata={
                    "resolver_match": getattr(request.resolver_match, "view_name", "")
                    if hasattr(request, "resolver_match")
                    else ""
                },
            )

        return response

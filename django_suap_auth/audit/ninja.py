from functools import wraps
from typing import Any, Callable

from .models import EventCategory, EventSeverity
from .services import record_audit_event


def audit_ninja_endpoint(operation_name: str = "", version: str = "v1") -> Callable:
    """Decorator utilitário para endpoints do Django Ninja (v1/v2)."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args: Any, **kwargs: Any) -> Any:
            op = operation_name or func.__name__
            try:
                response = func(request, *args, **kwargs)
                record_audit_event(
                    category=EventCategory.API_ACCESS,
                    event_type=f"api.ninja.{version}.{op}",
                    severity=EventSeverity.INFO,
                    request=request,
                    status_code=getattr(response, "status_code", 200),
                    metadata={"operation": op, "version": version},
                )
                return response
            except Exception as exc:
                record_audit_event(
                    category=EventCategory.API_ACCESS,
                    event_type=f"api.ninja.{version}.{op}.error",
                    severity=EventSeverity.CRITICAL,
                    request=request,
                    status_code=500,
                    metadata={
                        "operation": op,
                        "version": version,
                        "error": str(exc),
                    },
                )
                raise exc

        return wrapper

    return decorator

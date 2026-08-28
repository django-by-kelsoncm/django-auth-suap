from django.dispatch import receiver

from .models import EventCategory, EventSeverity
from .services import record_audit_event
from .signals import (
    suap_auth_failed,
    suap_auth_success,
    suap_impersonate_started,
    suap_impersonate_stopped,
    suap_jwt_issued,
    suap_jwt_refreshed,
)


@receiver(suap_auth_success)
def on_suap_auth_success(sender, request=None, user=None, suap_user_info=None, **kwargs):
    record_audit_event(
        category=EventCategory.AUTHENTICATION,
        event_type="auth.login.success",
        severity=EventSeverity.INFO,
        request=request,
        user=user,
        metadata={"provider": "suap"},
    )


@receiver(suap_auth_failed)
def on_suap_auth_failed(sender, request=None, reason="", details=None, **kwargs):
    record_audit_event(
        category=EventCategory.AUTHENTICATION,
        event_type="auth.login.failed",
        severity=EventSeverity.WARNING,
        request=request,
        metadata={"reason": reason, "details": details or {}},
    )


@receiver(suap_jwt_issued)
def on_suap_jwt_issued(sender, request=None, user=None, token_type="access", **kwargs):
    record_audit_event(
        category=EventCategory.AUTHENTICATION,
        event_type="auth.jwt.issued",
        severity=EventSeverity.INFO,
        request=request,
        user=user,
        metadata={"token_type": token_type},
    )


@receiver(suap_jwt_refreshed)
def on_suap_jwt_refreshed(sender, request=None, user=None, **kwargs):
    record_audit_event(
        category=EventCategory.AUTHENTICATION,
        event_type="auth.jwt.refreshed",
        severity=EventSeverity.INFO,
        request=request,
        user=user,
    )


@receiver(suap_impersonate_started)
def on_suap_impersonate_started(sender, request=None, impersonator=None, target_user=None, **kwargs):
    record_audit_event(
        category=EventCategory.IMPERSONATION,
        event_type="impersonate.start",
        severity=EventSeverity.WARNING,
        request=request,
        user=target_user,
        impersonator=impersonator,
        metadata={
            "impersonator_id": getattr(impersonator, "pk", None),
            "target_id": getattr(target_user, "pk", None),
        },
    )


@receiver(suap_impersonate_stopped)
def on_suap_impersonate_stopped(sender, request=None, impersonator=None, target_user=None, **kwargs):
    record_audit_event(
        category=EventCategory.IMPERSONATION,
        event_type="impersonate.stop",
        severity=EventSeverity.INFO,
        request=request,
        user=target_user,
        impersonator=impersonator,
    )

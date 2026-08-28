import gzip
import json
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import AuditEvent, EventCategory, EventSeverity

logger = logging.getLogger("django_suap_auth.audit")


def sanitize_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitiza dicionário de metadados removendo senhas e tokens brutos."""
    if not isinstance(data, dict):
        return {}
    sensitive_keys = {
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "suap_token",
    }
    sanitized = {}
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_metadata(v)
        else:
            sanitized[k] = v
    return sanitized


def record_audit_event(
    category: str,
    event_type: str,
    severity: str = EventSeverity.INFO,
    correlation_id: str = "",
    request=None,
    user=None,
    impersonator=None,
    application_name: str = "",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Cria e salva um registro AuditEvent, disparando checagens de alerta."""
    cfg = getattr(settings, "SUAP_AUTH", {})
    app_name = (
        application_name or cfg.get("APPLICATION_NAME") or getattr(settings, "SUAP_AUTH_APPLICATION_NAME", "default")
    )

    # Extrai do request se disponível
    ip_addr = None
    user_agent_str = ""
    req_path = ""
    req_method = ""

    if request:
        if not correlation_id and hasattr(request, "correlation_id"):
            correlation_id = request.correlation_id

        # Tenta obter IP de headers proxy ou REMOTE_ADDR
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip_addr = x_forwarded.split(",")[0].strip()
        else:
            ip_addr = request.META.get("REMOTE_ADDR")

        user_agent_str = request.META.get("HTTP_USER_AGENT", "")[:500]
        req_path = request.path[:500]
        req_method = request.method

        if not user and hasattr(request, "user") and request.user.is_authenticated:
            user = request.user

        # Trata sessão impersonada
        if not impersonator and hasattr(request, "session"):
            if "_impersonate_by" in request.session:
                imp_id = request.session.get("_impersonate_by")
                from django.contrib.auth import get_user_model

                User = get_user_model()
                try:
                    impersonator = User.objects.get(pk=imp_id)
                except User.DoesNotExist:
                    pass

    if not correlation_id:
        import uuid

        correlation_id = str(uuid.uuid4())

    user_ident = ""
    if user:
        user_ident = getattr(user, "username", getattr(user, "email", str(user.pk)))

    imp_ident = ""
    if impersonator:
        imp_ident = getattr(
            impersonator,
            "username",
            getattr(impersonator, "email", str(impersonator.pk)),
        )

    from django.apps import apps

    if not apps.is_installed("django_suap_auth.audit"):
        return None

    meta = sanitize_metadata(metadata or {})

    try:
        event = AuditEvent.objects.create(
            correlation_id=correlation_id,
            category=category,
            event_type=event_type,
            severity=severity,
            application_name=app_name,
            user=user if getattr(user, "pk", None) else None,
            user_identifier=user_ident,
            impersonator=impersonator if getattr(impersonator, "pk", None) else None,
            impersonator_identifier=imp_ident,
            ip_address=ip_addr,
            user_agent=user_agent_str,
            request_path=req_path,
            request_method=req_method,
            status_code=status_code,
            duration_ms=duration_ms,
            metadata=meta,
        )

        # Logger dual-write (para coletor stdout/SIEM)
        logger.info(
            f"[AUDIT] {event.event_type} | correlation_id={event.correlation_id} | "
            f"user={event.user_identifier} | ip={event.ip_address}"
        )

        # Avaliação de alertas automáticos se não for um evento do próprio alerta
        if category != EventCategory.SECURITY_ALERT:
            check_alert_rules(event)

        return event
    except Exception as e:
        logger.warning("Could not record audit event: %s", e)
        return None


def check_alert_rules(event: AuditEvent) -> None:
    """Verifica regras de anomalias (picos de falha, impersonate fora de hora, erros 401/403)."""
    now = timezone.now()

    # Regra 1: Falhas consecutivas de login SUAP
    failed_threshold = getattr(settings, "SUAP_AUTH_AUDIT_FAILED_LOGIN_THRESHOLD", 5)
    failed_minutes = getattr(settings, "SUAP_AUTH_AUDIT_FAILED_LOGIN_MINUTES", 5)

    if event.event_type in ["auth.login.failed", "auth.jwt.failed"]:
        min_ago = now - timedelta(minutes=failed_minutes)
        failed_count = AuditEvent.objects.filter(
            event_type__in=["auth.login.failed", "auth.jwt.failed"],
            timestamp__gte=min_ago,
        )
        if event.ip_address:
            failed_count = failed_count.filter(ip_address=event.ip_address)

        if failed_count.count() >= failed_threshold:
            trigger_security_alert(
                rule_name="Pico de Falhas de Autenticação SUAP",
                severity=EventSeverity.CRITICAL,
                details={
                    "count": failed_count.count(),
                    "ip": event.ip_address,
                    "target_user": event.user_identifier,
                },
            )

    # Regra 2: Impersonate iniciado fora de horário comercial
    night_start = getattr(settings, "SUAP_AUTH_AUDIT_IMPERSONATE_NIGHT_START", 22)
    morning_end = getattr(settings, "SUAP_AUTH_AUDIT_IMPERSONATE_MORNING_END", 6)

    if event.event_type == "impersonate.start":
        hour = event.timestamp.hour
        if hour >= night_start or hour < morning_end:
            trigger_security_alert(
                rule_name="Impersonate Fora de Horário Comercial",
                severity=EventSeverity.WARNING,
                details={
                    "impersonator": event.impersonator_identifier,
                    "target_user": event.user_identifier,
                    "hour": hour,
                },
            )

    # Regra 3: Abuso de erros 401/403 em APIs
    api_threshold = getattr(settings, "SUAP_AUTH_AUDIT_API_DENIED_THRESHOLD", 20)
    api_minutes = getattr(settings, "SUAP_AUTH_AUDIT_API_DENIED_MINUTES", 1)

    if event.status_code in [401, 403]:
        api_min_ago = now - timedelta(minutes=api_minutes)
        denied_count = AuditEvent.objects.filter(
            status_code__in=[401, 403],
            timestamp__gte=api_min_ago,
            ip_address=event.ip_address,
        ).count()
        if denied_count >= api_threshold:
            trigger_security_alert(
                rule_name="Possível Força Bruta ou Injeção em APIs (HTTP 401/403)",
                severity=EventSeverity.CRITICAL,
                details={
                    "count": denied_count,
                    "ip": event.ip_address,
                    "path": event.request_path,
                },
            )


def trigger_security_alert(rule_name: str, severity: str, details: Dict[str, Any]) -> AuditEvent:
    """Registra um SECURITY_ALERT e envia notificações pelos canais configurados."""
    alert_event = AuditEvent.objects.create(
        category=EventCategory.SECURITY_ALERT,
        event_type=f"security.alert.{rule_name.lower().replace(' ', '_')}",
        severity=severity,
        application_name=getattr(settings, "SUAP_AUTH_APPLICATION_NAME", "default"),
        metadata={"rule": rule_name, "details": details},
    )

    dispatch_notifications(alert_event, rule_name, details)
    return alert_event


def dispatch_notifications(alert_event: AuditEvent, rule_name: str, details: Dict[str, Any]) -> None:
    """Envia notificações para E-mail, Webhook HTTP e Telegram."""
    channels = getattr(
        settings,
        "SUAP_AUTH_AUDIT_CHANNELS",
        ["admin", "email", "webhook", "telegram"],
    )

    # Channel 1: E-mail
    if "email" in channels:
        recipient_list = getattr(settings, "SUAP_AUTH_AUDIT_NOTIFY_EMAILS", [])
        if recipient_list:
            try:
                subject = f"[{alert_event.severity}] Alerta de Auditoria: {rule_name}"
                details_json = json.dumps(details, indent=2)
                body = (
                    f"Alerta de Segurança Disparado:\nRegra: {rule_name}\n"
                    f"Gravidade: {alert_event.severity}\nDetalhes: {details_json}"
                )
                send_mail(
                    subject,
                    body,
                    getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                    recipient_list,
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Erro ao enviar e-mail de alerta: {e}")

    # Channel 2: Webhook HTTP
    if "webhook" in channels:
        webhook_url = getattr(settings, "SUAP_AUTH_AUDIT_WEBHOOK_URL", None)
        if webhook_url:
            try:
                requests.post(
                    webhook_url,
                    json={
                        "rule": rule_name,
                        "severity": alert_event.severity,
                        "details": details,
                        "timestamp": alert_event.timestamp.isoformat(),
                    },
                    timeout=5,
                )
            except Exception as e:
                logger.error(f"Erro ao enviar webhook de alerta: {e}")

    # Channel 3: Telegram Bot API
    if "telegram" in channels:
        bot_token = getattr(settings, "SUAP_AUTH_AUDIT_TELEGRAM_TOKEN", None)
        chat_id = getattr(settings, "SUAP_AUTH_AUDIT_TELEGRAM_CHAT_ID", None)
        if bot_token and chat_id:
            try:
                msg = f"🚨 *{alert_event.severity}*: {rule_name}\n`{json.dumps(details)}`"
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "Markdown",
                    },
                    timeout=5,
                )
            except Exception as e:
                logger.error(f"Erro ao enviar notificação Telegram: {e}")


def archive_audit_events(
    days_older: int = 365,
    output_path: Optional[str] = None,
    delete_archived: bool = True,
) -> int:
    """Exporta eventos mais antigos que N dias para JSONL comprimido (.gz) e opcionalmente remove do DB."""
    cutoff = timezone.now() - timedelta(days=days_older)
    queryset = AuditEvent.objects.filter(timestamp__lt=cutoff).order_by("timestamp")
    count = queryset.count()
    if count == 0:
        return 0

    if not output_path:
        filename = f"audit_archive_{cutoff.strftime('%Y%m%d')}_{count}_records.jsonl.gz"
        output_path = filename

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        for event in queryset.iterator():
            record = {
                "id": str(event.id),
                "correlation_id": event.correlation_id,
                "timestamp": event.timestamp.isoformat(),
                "category": event.category,
                "event_type": event.event_type,
                "severity": event.severity,
                "application_name": event.application_name,
                "user_identifier": event.user_identifier,
                "impersonator_identifier": event.impersonator_identifier,
                "ip_address": event.ip_address,
                "ip_hashed": event.ip_hashed,
                "user_agent": event.user_agent,
                "request_path": event.request_path,
                "request_method": event.request_method,
                "status_code": event.status_code,
                "duration_ms": event.duration_ms,
                "metadata": event.metadata,
            }
            f.write(json.dumps(record) + "\n")

    if delete_archived:
        queryset.delete()

    return count

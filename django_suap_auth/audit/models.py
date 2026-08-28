import hashlib
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def hash_ip(ip_address: str) -> str:
    """Gera um hash HMAC/SHA256 determinístico para o IP para uso em estatísticas LGPD."""
    if not ip_address:
        return ""
    salt = getattr(settings, "SUAP_AUTH_AUDIT_SALT", "suap_auth_audit_salt_2026")
    return hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()


class EventCategory(models.TextChoices):
    AUTHENTICATION = "AUTH", _("Autenticação OAuth2/JWT")
    IMPERSONATION = "IMPERSONATE", _("Sessão Impersonada")
    API_ACCESS = "API", _("Acesso a API / Endpoint")
    SECURITY_ALERT = "SECURITY", _("Alerta de Segurança")


class EventSeverity(models.TextChoices):
    INFO = "INFO", _("Informação")
    WARNING = "WARNING", _("Aviso / Suspeito")
    CRITICAL = "CRITICAL", _("Crítico / Falha de Segurança")


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    correlation_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text=_("UUID da requisição HTTP para rastreamento de fluxo."),
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    category = models.CharField(max_length=20, choices=EventCategory.choices, db_index=True)
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("Ex: auth.login.success, auth.jwt.issued, impersonate.start, api.ninja.access"),
    )
    severity = models.CharField(
        max_length=10,
        choices=EventSeverity.choices,
        default=EventSeverity.INFO,
        db_index=True,
    )
    application_name = models.CharField(
        max_length=100,
        db_index=True,
        default="default",
        help_text=_("Nome da aplicação consumidor (ex: sas-painel)"),
    )

    # Atores
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    user_identifier = models.CharField(
        max_length=150,
        blank=True,
        default="",
        db_index=True,
        help_text=_("Username/Matrícula preservado para integridade auditável"),
    )

    impersonator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events_as_impersonator",
    )
    impersonator_identifier = models.CharField(max_length=150, blank=True, default="", db_index=True)

    # Contexto Técnico HTTP e LGPD
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("IP bruto original (acesso restrito por permissão)"),
    )
    ip_hashed = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text=_("Hash SHA-256 do IP para dashboards e analytics sem PII"),
    )
    user_agent = models.TextField(blank=True, default="")
    request_path = models.CharField(max_length=500, blank=True, default="", db_index=True)
    request_method = models.CharField(max_length=10, blank=True, default="")
    status_code = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    duration_ms = models.FloatField(null=True, blank=True, help_text=_("Tempo de resposta em milissegundos"))

    # Metadados sanitizados
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Evento de Auditoria")
        verbose_name_plural = _("Eventos de Auditoria")
        ordering = ["-timestamp"]
        permissions = [
            ("view_raw_ip", "Pode visualizar o IP bruto nos logs de auditoria"),
        ]
        indexes = [
            models.Index(fields=["timestamp", "category"]),
            models.Index(fields=["application_name", "timestamp"]),
            models.Index(fields=["user_identifier", "timestamp"]),
            models.Index(fields=["correlation_id"]),
        ]

    def save(self, *args, **kwargs):
        if self.ip_address and not self.ip_hashed:
            self.ip_hashed = hash_ip(self.ip_address)
        super().save(*args, **kwargs)

    def __str__(self):
        user_str = self.user_identifier or "Anônimo"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.event_type} - {user_str}"

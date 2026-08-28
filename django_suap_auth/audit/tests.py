import os
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from .admin import AuditEventAdmin
from .models import AuditEvent, EventCategory, EventSeverity, hash_ip
from .ninja import audit_ninja_endpoint
from .services import (
    archive_audit_events,
    check_alert_rules,
    dispatch_notifications,
    record_audit_event,
    sanitize_metadata,
)
from .signals import (
    suap_auth_failed,
    suap_auth_success,
    suap_impersonate_started,
    suap_impersonate_stopped,
    suap_jwt_issued,
    suap_jwt_refreshed,
)

User = get_user_model()


class AuditAppConfigTests(TestCase):
    def test_apps_ready(self):
        config = apps.get_app_config("django_suap_auth_audit")
        config.ready()
        self.assertEqual(config.label, "django_suap_auth_audit")


class AuditModelTests(TestCase):
    def test_audit_event_creation_and_str(self):
        user = User.objects.create_user(username="testuser", email="test@example.com")
        event = AuditEvent.objects.create(
            correlation_id="corr-123",
            category=EventCategory.AUTHENTICATION,
            event_type="auth.login.success",
            user=user,
            user_identifier="testuser",
            ip_address="192.168.1.100",
        )
        self.assertTrue(event.ip_hashed)
        self.assertEqual(hash_ip("192.168.1.100"), event.ip_hashed)
        self.assertIn("auth.login.success", str(event))
        self.assertIn("testuser", str(event))

    def test_hash_ip_empty(self):
        self.assertEqual(hash_ip(""), "")
        self.assertEqual(hash_ip(None), "")


class AuditServicesTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="actor", email="actor@example.com")
        self.admin_user = User.objects.create_superuser(username="admin_actor", email="admin_actor@example.com")

    def test_sanitize_metadata(self):
        raw = {
            "normal": "value",
            "password": "secret_pass",
            "TOKEN": "token_val",
            "nested": {"access_token": "secret_jwt", "public": 123},
        }
        sanitized = sanitize_metadata(raw)
        self.assertEqual(sanitized["normal"], "value")
        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertEqual(sanitized["TOKEN"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["access_token"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["public"], 123)
        self.assertEqual(sanitize_metadata(None), {})

    def test_record_audit_event_with_request_and_impersonate(self):
        request = self.factory.get("/api/test/", HTTP_USER_AGENT="TestAgent/1.0")
        request.META["REMOTE_ADDR"] = "200.1.2.3"
        request.user = self.user
        request.correlation_id = "request-corr-id"
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session["_impersonate_by"] = self.admin_user.pk
        request.session.save()

        event = record_audit_event(
            category=EventCategory.API_ACCESS,
            event_type="api.test.access",
            request=request,
            status_code=200,
            duration_ms=15.5,
            metadata={"password": "123"},
        )
        self.assertEqual(event.correlation_id, "request-corr-id")
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.user_identifier, "actor")
        self.assertEqual(event.impersonator, self.admin_user)
        self.assertEqual(event.impersonator_identifier, "admin_actor")
        self.assertEqual(event.ip_address, "200.1.2.3")
        self.assertEqual(event.request_method, "GET")
        self.assertEqual(event.metadata["password"], "[REDACTED]")

    def test_record_audit_event_nonexistent_impersonator(self):
        request = self.factory.get("/test/")
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session["_impersonate_by"] = 999999
        request.session.save()

        event = record_audit_event(
            category=EventCategory.AUTHENTICATION,
            event_type="test.nonexistent",
            request=request,
        )
        self.assertIsNone(event.impersonator)

    def test_record_audit_event_with_x_forwarded_for(self):
        request = self.factory.get("/test/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2"
        event = record_audit_event(
            category=EventCategory.AUTHENTICATION,
            event_type="test.forwarded",
            request=request,
        )
        self.assertEqual(event.ip_address, "10.0.0.1")

    @patch("django.apps.apps.is_installed", return_value=False)
    def test_record_audit_event_uninstalled(self, mock_is_installed):
        event = record_audit_event(
            category=EventCategory.AUTHENTICATION,
            event_type="test.uninstalled",
        )
        self.assertIsNone(event)

    @patch.object(AuditEvent.objects, "create", side_effect=Exception("DB Error"))
    def test_record_audit_event_db_error(self, mock_create):
        event = record_audit_event(
            category=EventCategory.AUTHENTICATION,
            event_type="test.db_error",
        )
        self.assertIsNone(event)

    def test_check_alert_rules_failed_logins(self):
        now = timezone.now()
        for i in range(5):
            AuditEvent.objects.create(
                category=EventCategory.AUTHENTICATION,
                event_type="auth.login.failed",
                severity=EventSeverity.WARNING,
                ip_address="192.168.1.50",
                timestamp=now - timedelta(minutes=1),
            )
        event = AuditEvent.objects.last()
        check_alert_rules(event)

        alert = AuditEvent.objects.filter(category=EventCategory.SECURITY_ALERT).first()
        self.assertIsNotNone(alert)
        self.assertIn("Pico de Falhas", alert.metadata["rule"])

    def test_check_alert_rules_impersonate_off_hours(self):
        event = AuditEvent.objects.create(
            category=EventCategory.IMPERSONATION,
            event_type="impersonate.start",
            severity=EventSeverity.WARNING,
            impersonator_identifier="admin",
            user_identifier="victim",
        )
        AuditEvent.objects.filter(pk=event.pk).update(timestamp=timezone.now().replace(hour=23))
        event.refresh_from_db()
        check_alert_rules(event)
        alert = AuditEvent.objects.filter(category=EventCategory.SECURITY_ALERT).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.metadata["rule"], "Impersonate Fora de Horário Comercial")

    def test_check_alert_rules_api_denied_abuse(self):
        now = timezone.now()
        for i in range(20):
            AuditEvent.objects.create(
                category=EventCategory.API_ACCESS,
                event_type="api.ninja.access",
                status_code=401,
                ip_address="172.16.0.5",
                timestamp=now - timedelta(seconds=10),
            )
        event = AuditEvent.objects.last()
        check_alert_rules(event)
        alert = AuditEvent.objects.filter(category=EventCategory.SECURITY_ALERT).first()
        self.assertIsNotNone(alert)
        self.assertIn("Possível Força Bruta", alert.metadata["rule"])

    @patch("requests.post")
    @patch("django_suap_auth.audit.services.send_mail")
    @override_settings(
        SUAP_AUTH_AUDIT_CHANNELS=["email", "webhook", "telegram"],
        SUAP_AUTH_AUDIT_NOTIFY_EMAILS=["admin@example.com"],
        SUAP_AUTH_AUDIT_WEBHOOK_URL="https://hooks.example.com/test",
        SUAP_AUTH_AUDIT_TELEGRAM_TOKEN="123:TOKEN",
        SUAP_AUTH_AUDIT_TELEGRAM_CHAT_ID="999",
    )
    def test_dispatch_notifications(self, mock_send_mail, mock_post):
        alert_event = AuditEvent.objects.create(
            category=EventCategory.SECURITY_ALERT,
            event_type="security.alert.test",
            severity=EventSeverity.CRITICAL,
        )
        dispatch_notifications(alert_event, "Test Rule", {"key": "val"})

        self.assertTrue(mock_send_mail.called)
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.post", side_effect=Exception("Connection error"))
    @patch("django_suap_auth.audit.services.send_mail", side_effect=Exception("SMTP error"))
    @override_settings(
        SUAP_AUTH_AUDIT_CHANNELS=["email", "webhook", "telegram"],
        SUAP_AUTH_AUDIT_NOTIFY_EMAILS=["admin@example.com"],
        SUAP_AUTH_AUDIT_WEBHOOK_URL="https://hooks.example.com/test",
        SUAP_AUTH_AUDIT_TELEGRAM_TOKEN="123:TOKEN",
        SUAP_AUTH_AUDIT_TELEGRAM_CHAT_ID="999",
    )
    def test_dispatch_notifications_handles_exceptions(self, mock_send_mail, mock_post):
        alert_event = AuditEvent.objects.create(
            category=EventCategory.SECURITY_ALERT,
            event_type="security.alert.error_test",
            severity=EventSeverity.CRITICAL,
        )
        dispatch_notifications(alert_event, "Test Exception Rule", {})
        self.assertTrue(mock_send_mail.called)

    def test_archive_audit_events(self):
        old_time = timezone.now() - timedelta(days=400)
        e1 = AuditEvent.objects.create(
            category=EventCategory.AUTHENTICATION,
            event_type="old.event",
            correlation_id="old1",
        )
        AuditEvent.objects.filter(pk=e1.pk).update(timestamp=old_time)

        e2 = AuditEvent.objects.create(
            category=EventCategory.AUTHENTICATION,
            event_type="recent.event",
            correlation_id="recent1",
        )

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            count = archive_audit_events(days_older=365, output_path=tmp_path, delete_archived=True)
            self.assertEqual(count, 1)
            self.assertEqual(AuditEvent.objects.count(), 1)
            self.assertEqual(AuditEvent.objects.first().id, e2.id)
            self.assertTrue(os.path.exists(tmp_path))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        self.assertEqual(archive_audit_events(days_older=365), 0)

    def test_archive_audit_events_default_output_path(self):
        old_time = timezone.now() - timedelta(days=400)
        e1 = AuditEvent.objects.create(
            category=EventCategory.AUTHENTICATION,
            event_type="old.default_path",
            correlation_id="old_def",
        )
        AuditEvent.objects.filter(pk=e1.pk).update(timestamp=old_time)

        date_str = (timezone.now() - timedelta(days=365)).strftime("%Y%m%d")
        expected_filename = f"audit_archive_{date_str}_1_records.jsonl.gz"
        try:
            count = archive_audit_events(days_older=365, output_path=None, delete_archived=True)
            self.assertEqual(count, 1)
            self.assertTrue(os.path.exists(expected_filename))
        finally:
            if os.path.exists(expected_filename):
                os.remove(expected_filename)


class AuditBackendTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_backend_auth_failure_triggers_signal(self):
        from django_suap_auth.backends import SuapAuthBackend

        backend = SuapAuthBackend()
        request = self.factory.get("/")
        with patch.object(SuapAuthBackend, "get_or_create_user", side_effect=Exception("User error")):
            with self.assertRaises(Exception):
                backend.authenticate(request, suap_user_info={"identificacao": "user1"})
        self.assertTrue(AuditEvent.objects.filter(event_type="auth.login.failed").exists())


class AuditMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_correlation_middleware(self):
        from .middleware import CorrelationMiddleware

        middleware = CorrelationMiddleware(get_response=lambda r: None)
        request = self.factory.get("/test/", HTTP_X_CORRELATION_ID="existing-id")
        middleware.process_request(request)
        self.assertEqual(request.correlation_id, "existing-id")

        from django.http import HttpResponse

        response = HttpResponse("OK")
        middleware.process_response(request, response)
        self.assertEqual(response["X-Correlation-ID"], "existing-id")

    def test_audit_middleware_captures_api(self):
        from .middleware import AuditMiddleware

        middleware = AuditMiddleware(get_response=lambda r: None)
        request = self.factory.get("/api/v1/users/")
        middleware.process_request(request)

        from django.http import HttpResponse

        response = HttpResponse("Forbidden", status=403)
        middleware.process_response(request, response)

        event = AuditEvent.objects.filter(category=EventCategory.API_ACCESS).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status_code, 403)
        self.assertEqual(event.severity, EventSeverity.WARNING)

    def test_audit_middleware_captures_server_error(self):
        from .middleware import AuditMiddleware

        middleware = AuditMiddleware(get_response=lambda r: None)
        request = self.factory.post("/api/v1/crash/")
        middleware.process_request(request)

        from django.http import HttpResponse

        response = HttpResponse("Error", status=500)
        middleware.process_response(request, response)

        event = AuditEvent.objects.filter(category=EventCategory.API_ACCESS).first()
        self.assertEqual(event.severity, EventSeverity.CRITICAL)

    def test_audit_middleware_ignores_static(self):
        from .middleware import AuditMiddleware

        middleware = AuditMiddleware(get_response=lambda r: None)
        request = self.factory.get("/static/css/style.css")
        middleware.process_request(request)

        from django.http import HttpResponse

        response = HttpResponse("OK", status=200)
        middleware.process_response(request, response)
        self.assertEqual(AuditEvent.objects.count(), 0)


class AuditNinjaTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_audit_ninja_endpoint_success(self):
        @audit_ninja_endpoint(operation_name="get_users", version="v2")
        def mock_ninja_endpoint(request):
            from django.http import JsonResponse

            return JsonResponse({"users": []}, status=200)

        request = self.factory.get("/api/v2/users/")
        response = mock_ninja_endpoint(request)
        self.assertEqual(response.status_code, 200)

        event = AuditEvent.objects.filter(event_type="api.ninja.v2.get_users").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.metadata["version"], "v2")

    def test_audit_ninja_endpoint_error(self):
        @audit_ninja_endpoint(operation_name="fail_op", version="v1")
        def mock_failing_endpoint(request):
            raise ValueError("Ninja internal error")

        request = self.factory.get("/api/v1/fail/")
        with self.assertRaises(ValueError):
            mock_failing_endpoint(request)

        event = AuditEvent.objects.filter(event_type="api.ninja.v1.fail_op.error").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.severity, EventSeverity.CRITICAL)


class AuditReceiversTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="suapuser", email="suap@example.com")
        self.admin = User.objects.create_superuser(username="adminuser", email="admin@example.com")

    def test_auth_signals(self):
        request = self.factory.get("/login/callback/")
        suap_auth_success.send(sender=self.__class__, request=request, user=self.user, suap_user_info={})
        self.assertTrue(AuditEvent.objects.filter(event_type="auth.login.success", user=self.user).exists())

        suap_auth_failed.send(sender=self.__class__, request=request, reason="Invalid state")
        self.assertTrue(AuditEvent.objects.filter(event_type="auth.login.failed").exists())

    def test_jwt_signals(self):
        request = self.factory.post("/api/token/pair/")
        suap_jwt_issued.send(sender=self.__class__, request=request, user=self.user, token_type="pair")
        self.assertTrue(AuditEvent.objects.filter(event_type="auth.jwt.issued").exists())

        suap_jwt_refreshed.send(sender=self.__class__, request=request, user=self.user)
        self.assertTrue(AuditEvent.objects.filter(event_type="auth.jwt.refreshed").exists())

    def test_impersonate_signals(self):
        request = self.factory.get("/impersonate/testuser/")
        suap_impersonate_started.send(
            sender=self.__class__,
            request=request,
            impersonator=self.admin,
            target_user=self.user,
        )
        self.assertTrue(AuditEvent.objects.filter(event_type="impersonate.start", impersonator=self.admin).exists())

        suap_impersonate_stopped.send(
            sender=self.__class__,
            request=request,
            impersonator=self.admin,
            target_user=self.user,
        )
        self.assertTrue(AuditEvent.objects.filter(event_type="impersonate.stop").exists())


class AuditAdminAndViewsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(username="admin", email="admin@example.com")

    def test_dashboard_view_periods(self):
        from django_suap_auth.audit.views import AuditDashboardView

        view = AuditDashboardView.as_view()
        for p in ["24h", "7d", "30d"]:
            request = self.factory.get(f"/admin/django_suap_auth_audit/auditevent/dashboard/?period={p}")
            request.user = self.admin_user
            middleware = SessionMiddleware(lambda r: None)
            middleware.process_request(request)
            request.session.save()

            response = view(request)
            self.assertEqual(response.status_code, 200)

    def test_audit_admin_display_ip_permissions(self):
        event = AuditEvent.objects.create(
            category=EventCategory.AUTHENTICATION,
            event_type="test.ip",
            ip_address="192.168.1.200",
        )
        admin_obj = AuditEventAdmin(AuditEvent, None)

        request_normal = self.factory.get("/")
        normal_user = User.objects.create_user(username="staff_user", is_staff=True)
        request_normal.user = normal_user
        admin_obj.get_queryset(request_normal)
        displayed_ip = admin_obj.display_ip(event)
        self.assertNotIn("192.168.1.200", displayed_ip)

        request_priv = self.factory.get("/")
        request_priv.user = self.admin_user
        admin_obj.get_queryset(request_priv)
        self.assertEqual(admin_obj.display_ip(event), "192.168.1.200")

    def test_audit_admin_custom_urls_and_permissions(self):
        from django.contrib.admin import AdminSite

        site = AdminSite()
        admin_obj = AuditEventAdmin(AuditEvent, site)
        urls = admin_obj.get_urls()
        self.assertTrue(len(urls) > 0)

        request = self.factory.get("/")
        request.user = self.admin_user
        self.assertFalse(admin_obj.has_add_permission(request))
        self.assertFalse(admin_obj.has_change_permission(request))
        self.assertFalse(admin_obj.has_delete_permission(request))

        event = AuditEvent.objects.create(category="AUTH", event_type="t")
        self.assertIn("2026", admin_obj.timestamp_format(event))
        self.assertIn("Crítico", admin_obj.severity_badge(AuditEvent(severity=EventSeverity.CRITICAL)))

    def test_audit_archive_management_command(self):
        out = tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False)
        out_path = out.name
        out.close()
        try:
            call_command("audit_archive", "--days", "365", "--output", out_path, "--no-delete")
            self.assertTrue(os.path.exists(out_path))
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    def test_urls_import(self):
        import django_suap_auth.audit.urls as audit_urls

        self.assertTrue(hasattr(audit_urls, "urlpatterns"))

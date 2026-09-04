from unittest.mock import MagicMock, patch

import pytest
import requests
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import override_settings

from django_suap_auth.backends import SuapAuthBackend
from django_suap_auth.client import SuapOAuth2Client
from django_suap_auth.erros.admin import SincronizacaoErroAdmin
from django_suap_auth.erros.models import SincronizacaoErro
from django_suap_auth.erros.services import (
    report_sync_error_to_sentry,
    save_sync_error,
    save_sync_errors_for_user,
)
from django_suap_auth.exceptions import SuapUserInfoError
from django_suap_auth.fetchers import DefaultEndpointsUserInfoFetcher
from django_suap_auth.views import SuapCallbackView

User = get_user_model()


@pytest.mark.django_db
def test_sincronizacao_erro_model():
    user = User.objects.create(username="testuser")
    erro = SincronizacaoErro.objects.create(
        usuario=user,
        endpoint="/api/rh/meus-dados/",
        status_code=500,
        mensagem_erro="Internal Server Error detail message",
    )

    assert erro.usuario == user
    assert erro.endpoint == "/api/rh/meus-dados/"
    assert erro.status_code == 500
    assert "Erro em /api/rh/meus-dados/ [500]: Internal Server Error detail message" in str(erro)
    assert erro.history.count() == 1


@pytest.mark.django_db
def test_sincronizacao_erro_model_str_without_status_code():
    erro = SincronizacaoErro.objects.create(
        usuario=None,
        endpoint="/api/rh/meus-dados/",
        status_code=None,
        mensagem_erro="Connection Error",
    )
    assert str(erro) == "Erro em /api/rh/meus-dados/: Connection Error"


def test_sincronizacao_erro_admin():
    site = admin.AdminSite()
    admin_obj = SincronizacaoErroAdmin(SincronizacaoErro, site)
    assert "usuario" in admin_obj.list_display
    assert "endpoint" in admin_obj.list_display
    assert "status_code" in admin_obj.list_display


@pytest.mark.django_db
def test_report_sync_error_to_sentry_not_initialized():
    # Calling when sentry is not initialized should not raise exceptions
    report_sync_error_to_sentry(ValueError("test error"), endpoint="/api/test", status_code=400)


@pytest.mark.django_db
def test_report_sync_error_to_sentry_initialized():
    mock_sentry = MagicMock()
    mock_sentry.is_initialized.return_value = True
    scope_mock = MagicMock()
    mock_sentry.push_scope.return_value.__enter__.return_value = scope_mock

    user = User.objects.create(username="sentryuser")

    with patch.dict("sys.modules", {"sentry_sdk": mock_sentry}):
        report_sync_error_to_sentry(ValueError("sentry test"), endpoint="/api/sentry", status_code=500, user=user)
        mock_sentry.capture_exception.assert_called_once()
        scope_mock.set_extra.assert_any_call("endpoint", "/api/sentry")
        scope_mock.set_extra.assert_any_call("status_code", 500)
        scope_mock.set_user.assert_called_once_with({"id": user.pk, "username": "sentryuser"})

        # String error message branch
        mock_sentry.reset_mock()
        report_sync_error_to_sentry("string message", endpoint="/api/sentry2", status_code=500)
        mock_sentry.capture_message.assert_called_once_with("string message")


@pytest.mark.django_db
def test_report_sync_error_to_sentry_ignores_404_and_403():
    mock_sentry = MagicMock()
    mock_sentry.is_initialized.return_value = True

    with patch.dict("sys.modules", {"sentry_sdk": mock_sentry}):
        # Explicit status_code 404
        report_sync_error_to_sentry(ValueError("404 error"), endpoint="/api/not-found", status_code=404)
        mock_sentry.capture_exception.assert_not_called()

        # Exception with status_code 403 attribute
        exc_403 = SuapUserInfoError("Forbidden", status_code=403)
        report_sync_error_to_sentry(exc_403, endpoint="/api/forbidden")
        mock_sentry.capture_exception.assert_not_called()


@pytest.mark.django_db
def test_report_sync_error_to_sentry_exception_handling():
    mock_sentry = MagicMock()
    mock_sentry.is_initialized.side_effect = Exception("sentry fail")
    with patch.dict("sys.modules", {"sentry_sdk": mock_sentry}):
        # Should gracefully log warning and not raise
        report_sync_error_to_sentry(ValueError("err"))


@pytest.mark.django_db
def test_save_sync_error_db_exception():
    with patch("django_suap_auth.erros.models.SincronizacaoErro.objects.create", side_effect=Exception("db fail")):
        res = save_sync_error("/api/test", 500, "error")
        assert res is None


@pytest.mark.django_db
def test_save_sync_errors_for_user_empty():
    assert save_sync_errors_for_user(None, []) == []


@pytest.mark.django_db
@override_settings(INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "django_suap_auth"])
def test_save_sync_error_app_not_installed():
    res = save_sync_error("/api/test", 404, "not found")
    assert res is None


@pytest.mark.django_db
def test_fetcher_secondary_endpoint_failure_records_sync_error():
    client = MagicMock(spec=SuapOAuth2Client)

    def mock_get_endpoint_data(access_token, path_or_url):
        if path_or_url == "/api/rh/eu/":
            return {"identificacao": "12345", "nome_registro": "João Silva"}
        elif path_or_url == "/api/rh/meus-dados/":
            resp = requests.Response()
            resp.status_code = 404
            raise SuapUserInfoError("Failed to fetch endpoint '/api/rh/meus-dados/': 404 Client Error", status_code=404)
        return {}

    client.get_endpoint_data.side_effect = mock_get_endpoint_data

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            "/api/rh/meus-dados/",
        ]
    }
    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    user_info = fetcher.fetch(client, "fake_token")

    assert "_sync_errors" in user_info
    assert len(user_info["_sync_errors"]) == 1
    err = user_info["_sync_errors"][0]
    assert err["endpoint"] == "/api/rh/meus-dados/"
    assert err["status_code"] == 404

    backend = SuapAuthBackend()
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None

    db_errors = SincronizacaoErro.objects.filter(usuario=user)
    assert db_errors.count() == 1
    assert db_errors.first().endpoint == "/api/rh/meus-dados/"
    assert db_errors.first().status_code == 404


@pytest.mark.django_db
def test_fetcher_for_each_error_records_sync_error():
    client = MagicMock(spec=SuapOAuth2Client)

    def mock_get_endpoint_data(access_token, path_or_url):
        if path_or_url == "/api/rh/eu/":
            return {"identificacao": "12345", "periodos": [{"semestre": "2024.1"}]}
        elif path_or_url == "/api/ensino/diarios/2024.1/":
            resp = requests.Response()
            resp.status_code = 500
            raise SuapUserInfoError(
                "Failed to fetch endpoint '/api/ensino/diarios/2024.1/': 500 Server Error", status_code=500
            )
        return {}

    client.get_endpoint_data.side_effect = mock_get_endpoint_data

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            {
                "endpoint": "/api/ensino/diarios/{semestre}/",
                "for_each": "periodos",
                "namespace": "diarios",
            },
        ]
    }
    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    user_info = fetcher.fetch(client, "fake_token")

    assert "_sync_errors" in user_info
    assert len(user_info["_sync_errors"]) == 1
    assert user_info["_sync_errors"][0]["endpoint"] == "/api/ensino/diarios/2024.1/"
    assert user_info["_sync_errors"][0]["status_code"] == 500


@pytest.mark.django_db
def test_callback_view_authentication_failure_saves_sync_errors():
    user_info = {
        "_sync_errors": [{"endpoint": "/api/failed/", "status_code": 503, "mensagem_erro": "Service Unavailable"}]
    }
    with (
        patch("django_suap_auth.views.get_oauth2_client") as mock_get_client,
        patch("django_suap_auth.views.authenticate", return_value=None),
    ):
        mock_client = MagicMock()
        mock_client.exchange_code_for_token.return_value = {"access_token": "token123"}
        mock_client.get_user_info.return_value = user_info
        mock_get_client.return_value = mock_client

        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/auth/suap/callback/?code=123&state=teststate")
        request.session = {"suap_oauth2_state": "teststate"}
        setattr(request, "_messages", FallbackStorage(request))

        view = SuapCallbackView()
        res = view.get(request)
        assert res.status_code == 302

        db_errors = SincronizacaoErro.objects.filter(usuario=None)
        assert db_errors.count() == 1
        assert db_errors.first().endpoint == "/api/failed/"
        assert db_errors.first().status_code == 503

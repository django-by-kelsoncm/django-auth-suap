import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests
import responses
import responses as responses_lib
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from django_suap_auth.backends import SuapAuthBackend, _filter_fields
from django_suap_auth.client import AVAILABLE_SCOPES, SuapClient, SuapOAuth2Client
from django_suap_auth.exceptions import (
    SuapAPIError,
    SuapStateMismatchError,
    SuapTokenError,
    SuapUserInfoError,
    SuapUserNotAllowedError,
)
from django_suap_auth.fetchers import (
    BaseUserInfoFetcher,
    DefaultEndpointsUserInfoFetcher,
    get_user_info_fetchers,
    resolve_callable,
    resolve_callable_or_class,
    run_user_info_fetcher_chain,
)
from django_suap_auth.jwt_views import (
    BaseSuapTokenView,
    SuapTokenObtainPairView,
    SuapTokenPairView,
    SuapTokenRefreshView,
    SuapTokenVerifyView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django_suap_auth.mappers import (
    BaseSuapUserMapper,
    BaseUserMapper,
    DefaultAttrMapUserMapper,
    DefaultSuapUserMapper,
    _call_transformer,
    _extract_nested,
    get_user_info_mappers,
    run_user_info_mapper_chain,
)
from django_suap_auth.transformers import fetch_image_file, format_cpf, parse_date, to_bool, to_lower, to_upper
from django_suap_auth.utils import (
    apply_user_attr_map,
    generate_state,
    get_oauth2_client,
    get_suap_settings,
    get_user_mapper,
)


@pytest.fixture
def client_fixture():
    return Client()


# ---------------------------------------------------------------------------
# 1. Backends Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_authenticate_returns_none_without_user_info():
    backend = SuapAuthBackend()
    result = backend.authenticate(None, suap_user_info=None)
    assert result is None


@pytest.mark.django_db
def test_authenticate_creates_user():
    backend = SuapAuthBackend()
    user_info = {"identificacao": "20211234567", "nome_usual": "João Silva", "email": "joao@ifrn.edu.br"}
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None
    assert user.username == "20211234567"
    assert user.email == "joao@ifrn.edu.br"
    assert user.is_active is True


@pytest.mark.django_db
def test_authenticate_updates_existing_user():
    User = get_user_model()
    User.objects.create_user(username="20211234567", email="old@ifrn.edu.br")

    backend = SuapAuthBackend()
    user_info = {"identificacao": "20211234567", "nome_usual": "João Silva", "email": "new@ifrn.edu.br"}
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None
    assert user.email == "new@ifrn.edu.br"


@pytest.mark.django_db
def test_authenticate_returns_none_when_lookup_field_missing():
    backend = SuapAuthBackend()
    user_info = {"nome_usual": "João Silva"}  # no identificacao
    result = backend.authenticate(None, suap_user_info=user_info)
    assert result is None


@pytest.mark.django_db
def test_authenticate_reactivates_inactive_user():
    User = get_user_model()
    User.objects.create_user(username="20211234567", email="joao@ifrn.edu.br", is_active=False)

    backend = SuapAuthBackend()
    user_info = {"identificacao": "20211234567", "email": "joao@ifrn.edu.br"}
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None
    assert user.is_active is True


@pytest.mark.django_db
def test_get_user_returns_user():
    User = get_user_model()
    created = User.objects.create_user(username="20211234567")
    backend = SuapAuthBackend()
    user = backend.get_user(created.pk)
    assert user == created


@pytest.mark.django_db
def test_get_user_returns_none_for_nonexistent():
    backend = SuapAuthBackend()
    result = backend.get_user(99999)
    assert result is None


@pytest.mark.django_db
def test_authenticate_with_json_field(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "USER_JSON_FIELD": "last_name",  # reuse last_name for JSON storage in tests
    }
    backend = SuapAuthBackend()
    user_info = {"identificacao": "20211234567", "email": "joao@ifrn.edu.br"}
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None
    assert user.username == "20211234567"


@pytest.mark.django_db
def test_authenticate_with_unsupported_json_field(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "USER_JSON_FIELD": "non_existent_json_field",
    }
    backend = SuapAuthBackend()
    user_info = {"identificacao": "20219999999", "email": "novo@ifrn.edu.br"}
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None
    assert user.username == "20219999999"


@pytest.mark.django_db
def test_first_user_defaults_to_staff_and_superuser():
    User = get_user_model()
    User.objects.all().delete()
    backend = SuapAuthBackend()
    user_info = {"identificacao": "first_user", "email": "first@ifrn.edu.br"}
    user = backend.authenticate(None, suap_user_info=user_info)
    assert user is not None
    assert user.is_staff is True
    assert user.is_superuser is True

    # Second user created should not get first_user_defaults
    user2_info = {"identificacao": "second_user", "email": "second@ifrn.edu.br"}
    user2 = backend.authenticate(None, suap_user_info=user2_info)
    assert user2 is not None
    assert user2.is_staff is False
    assert user2.is_superuser is False


def test_filter_fields_allowed_list():
    attrs = {"username": "user1", "email": "a@b.com", "first_name": "John"}
    filtered = _filter_fields(attrs, allowed=["username", "email"])
    assert filtered == {"username": "user1", "email": "a@b.com"}


@pytest.mark.django_db
def test_backend_create_user_false_raises():
    backend = SuapAuthBackend()
    cfg = {
        "user_lookup_field": "username",
        "create_user": False,
        "user_attr_map": {"username": "identificacao"},
        "json_field": None,
    }
    with pytest.raises(SuapUserNotAllowedError):
        backend.get_or_create_user("username", "non_existent_user", {}, cfg)


@pytest.mark.django_db
def test_backend_first_user_defaults(settings):
    User = get_user_model()
    User.objects.all().delete()

    backend = SuapAuthBackend()
    cfg = {
        "user_lookup_field": "username",
        "create_user": True,
        "first_user_defaults": {"is_superuser": True, "is_staff": True},
        "user_defaults": {"is_active": True},
        "update_fields_on_create": None,
    }
    user = backend.create_user("username", "admin_user", {}, cfg)
    assert user.is_superuser is True
    assert user.is_staff is True


# ---------------------------------------------------------------------------
# 2. Client Tests
# ---------------------------------------------------------------------------


def make_client(**kwargs):
    return SuapOAuth2Client(
        client_id="test-client-id",
        client_secret="test-secret",
        redirect_uri="http://localhost/callback/",
        **kwargs,
    )


def test_client_defaults():
    client_obj = make_client()
    assert client_obj.base_url == "https://suap.ifrn.edu.br"
    assert client_obj.scopes == ["identificacao", "email"]


def test_client_custom_base_url():
    client_obj = make_client(base_url="https://suap.example.com/")
    assert client_obj.base_url == "https://suap.example.com"


def test_client_custom_scopes():
    client_obj = make_client(scopes=["identificacao", "email", "dados_academicos"])
    assert "dados_academicos" in client_obj.scopes


def test_available_scopes_list():
    assert "identificacao" in AVAILABLE_SCOPES
    assert "email" in AVAILABLE_SCOPES
    assert "documentos_pessoais" in AVAILABLE_SCOPES
    assert "dados_academicos" in AVAILABLE_SCOPES
    assert "dados_pessoais" in AVAILABLE_SCOPES
    assert "reitoria" in AVAILABLE_SCOPES


def test_get_authorization_url_contains_required_params():
    client_obj = make_client()
    url = client_obj.get_authorization_url("test-state-123")
    assert "response_type=code" in url
    assert "client_id=test-client-id" in url
    assert "state=test-state-123" in url
    assert "suap.ifrn.edu.br" in url


def test_get_authorization_url_contains_scopes():
    client_obj = make_client(scopes=["identificacao", "email"])
    url = client_obj.get_authorization_url("state")
    assert "scope=" in url
    assert "identificacao" in url


@responses_lib.activate
def test_exchange_code_for_token_success():
    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        json={"access_token": "abc123", "token_type": "Bearer"},
        status=200,
    )
    client_obj = make_client()
    result = client_obj.exchange_code_for_token("auth-code-xyz")
    assert result["access_token"] == "abc123"


@responses_lib.activate
def test_exchange_code_for_token_http_error():
    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        json={"error": "invalid_grant"},
        status=400,
    )
    client_obj = make_client()
    with pytest.raises(SuapTokenError):
        client_obj.exchange_code_for_token("bad-code")


@responses_lib.activate
def test_exchange_code_for_token_connection_error():
    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        body=Exception("connection refused"),
    )
    client_obj = make_client()
    with pytest.raises(SuapTokenError):
        client_obj.exchange_code_for_token("code")


@responses_lib.activate
def test_get_user_info_success():
    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        json={"identificacao": "20211234567", "nome_usual": "João Silva", "email": "joao@ifrn.edu.br"},
        status=200,
    )
    client_obj = make_client()
    result = client_obj.get_user_info("access-token-xyz")
    assert result["identificacao"] == "20211234567"
    assert result["email"] == "joao@ifrn.edu.br"


@responses_lib.activate
def test_get_user_info_http_error():
    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        json={"detail": "Authentication credentials were not provided."},
        status=401,
    )
    client_obj = make_client()
    with pytest.raises(SuapUserInfoError):
        client_obj.get_user_info("bad-token")


@responses_lib.activate
def test_get_user_info_connection_error():
    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        body=Exception("connection refused"),
    )
    client_obj = make_client()
    with pytest.raises(SuapUserInfoError):
        client_obj.get_user_info("token")


@responses_lib.activate
def test_exchange_code_request_exception():
    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        body=requests.Timeout("timeout"),
    )
    client_obj = make_client()
    with pytest.raises(SuapTokenError):
        client_obj.exchange_code_for_token("auth-code")


@responses_lib.activate
def test_get_user_info_request_exception():
    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        body=requests.ConnectionError("connection error"),
    )
    client_obj = make_client()
    with pytest.raises(SuapUserInfoError):
        client_obj.get_user_info("token")


@responses.activate
def test_client_get_endpoint_data_full_url():
    client_obj = SuapOAuth2Client(
        client_id="id",
        client_secret="sec",
        redirect_uri="http://localhost/",
        base_url="https://suap.ifrn.edu.br",
    )
    responses.add(
        responses.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        json={"identificacao": "123"},
        status=200,
    )
    data = client_obj.get_endpoint_data("token", "https://suap.ifrn.edu.br/api/rh/eu/")
    assert data["identificacao"] == "123"


# ---------------------------------------------------------------------------
# 3. Fetchers Tests
# ---------------------------------------------------------------------------


def test_base_user_info_fetcher():
    fetcher = BaseUserInfoFetcher()
    info = fetcher.fetch(None, "token", {"initial": "val"})
    assert info == {"initial": "val"}


def test_fetchers_resolve_callable():
    assert resolve_callable(BaseUserInfoFetcher) is BaseUserInfoFetcher
    assert resolve_callable("django_suap_auth.fetchers.BaseUserInfoFetcher") is BaseUserInfoFetcher
    assert resolve_callable_or_class(BaseUserInfoFetcher) is BaseUserInfoFetcher
    with pytest.raises(TypeError):
        resolve_callable(12345)


def test_default_endpoints_user_info_fetcher():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.side_effect = lambda token, path: {
        "/api/rh/eu/": {"identificacao": "2080882", "email": "kelson@ifrn.edu.br"},
        "/api/rh/meus-dados/": {"rg": "123456", "tipo_sanguineo": "A+"},
        "/api/rh/meus-vinculos/": {"results": [{"id": 1, "tipo": "servidor"}], "count": 1},
    }.get(path, {})

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            "/api/rh/meus-dados/",
            {
                "endpoint": "/api/rh/meus-vinculos/",
                "namespace": "vinculos",
                "extract_list": "results",
            },
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-access-token")

    assert result["identificacao"] == "2080882"
    assert result["email"] == "kelson@ifrn.edu.br"
    assert result["rg"] == "123456"
    assert result["tipo_sanguineo"] == "A+"
    assert result["vinculos"] == [{"id": 1, "tipo": "servidor"}]


class CustomExternalLdapFetcher(BaseUserInfoFetcher):
    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        user_info["ldap_group"] = "sysadmins"
        return user_info


def test_run_user_info_fetcher_chain(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "USER_INFO_FETCHERS": [
            DefaultEndpointsUserInfoFetcher,
            CustomExternalLdapFetcher,
        ],
        "USER_INFO_ENDPOINTS": ["/api/rh/eu/"],
    }

    mock_client = MagicMock()
    mock_client.get_endpoint_data.return_value = {"identificacao": "2080882"}

    cfg = get_suap_settings()
    res = run_user_info_fetcher_chain(mock_client, "fake-token", cfg=cfg)

    assert res["identificacao"] == "2080882"
    assert res["ldap_group"] == "sysadmins"


def test_default_endpoints_user_info_fetcher_dynamic_url():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.side_effect = lambda token, path: {
        "/api/rh/eu/": {"identificacao": "2080882"},
        "/api/rh/servidores_funcao_ativa/?matricula=2080882": {
            "results": [{"id": 100, "nome": "Kelson da Costa Medeiros"}]
        },
    }.get(path, {})

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            {
                "endpoint": "/api/rh/servidores_funcao_ativa/?matricula={identificacao}",
                "namespace": "servidores_funcao_ativa",
                "extract_list": "results",
            },
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-token")

    assert result["identificacao"] == "2080882"
    assert result["servidores_funcao_ativa"] == [{"id": 100, "nome": "Kelson da Costa Medeiros"}]


def test_default_endpoints_user_info_fetcher_for_each():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.side_effect = lambda token, path: {
        "/api/ensino/periodos/": {"results": [{"semestre": "2015.2"}]},
        "/api/ensino/diarios/2015.2/": {"results": [{"id": 6793, "disciplina": "FIC.0520"}]},
    }.get(path, {})

    cfg = {
        "user_info_endpoints": [
            {
                "endpoint": "/api/ensino/periodos/",
                "namespace": "periodos",
                "extract_list": "results",
            },
            {
                "endpoint": "/api/ensino/diarios/{semestre}/",
                "for_each": "periodos",
                "namespace": "diarios",
                "extract_list": "results",
            },
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-token")

    assert result["periodos"] == [{"semestre": "2015.2"}]
    assert result["diarios"] == [{"id": 6793, "disciplina": "FIC.0520"}]


def test_secondary_endpoint_failure_is_non_fatal():
    mock_client = MagicMock()

    def side_effect(token, path):
        if path == "/api/rh/eu/":
            return {"identificacao": "2080882", "email": "kelson@ifrn.edu.br"}
        raise SuapUserInfoError(f"Failed to fetch endpoint '{path}': 404 Not Found")

    mock_client.get_endpoint_data.side_effect = side_effect

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            "/api/ensino/meus-dados-aluno/",
            {"endpoint": "/api/rh/meus-dados/", "required": False},
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-token")

    assert result["identificacao"] == "2080882"
    assert result["email"] == "kelson@ifrn.edu.br"


def test_primary_endpoint_failure_raises():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.side_effect = SuapUserInfoError("Failed to fetch primary endpoint: 500")

    cfg = {"user_info_endpoints": ["/api/rh/eu/"]}

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    with pytest.raises(SuapUserInfoError):
        fetcher.fetch(mock_client, "fake-token")


def test_secondary_endpoint_dict_spec_failure_is_non_fatal():
    mock_client = MagicMock()

    def side_effect(token, path):
        if path == "/api/rh/eu/":
            return {"identificacao": "2080882"}
        raise SuapUserInfoError(f"Failed: {path}")

    mock_client.get_endpoint_data.side_effect = side_effect

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            {"endpoint": "/api/rh/meus-dados/"},
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-token")
    assert result["identificacao"] == "2080882"


def test_base_user_info_fetcher_none_user_info():
    fetcher = BaseUserInfoFetcher()
    info = fetcher.fetch(None, "token", user_info=None)
    assert info == {}


def test_fetcher_formatting_errors_and_edge_cases():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.return_value = {"key": "val"}

    # String endpoint formatting error
    cfg = {"user_info_endpoints": ["/api/test/{missing_key}/"]}
    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    res = fetcher.fetch(mock_client, "token", user_info={})
    assert res == {}

    # Empty dict endpoint spec (no endpoint key)
    cfg2 = {"user_info_endpoints": [{}]}
    fetcher2 = DefaultEndpointsUserInfoFetcher(suap_settings=cfg2)
    res2 = fetcher2.fetch(mock_client, "token", user_info={})
    assert res2 == {}

    # Dict endpoint formatting error
    cfg3 = {"user_info_endpoints": [{"endpoint": "/api/test/{missing}/"}]}
    fetcher3 = DefaultEndpointsUserInfoFetcher(suap_settings=cfg3)
    res3 = fetcher3.fetch(mock_client, "token", user_info={})
    assert res3 == {}

    # Generic Exception during endpoint fetch (not SuapUserInfoError)
    mock_client_err = MagicMock()
    mock_client_err.get_endpoint_data.side_effect = RuntimeError("Generic network issue")
    cfg4 = {"user_info_endpoints": ["/api/error/"]}
    fetcher4 = DefaultEndpointsUserInfoFetcher(suap_settings=cfg4)
    res4 = fetcher4.fetch(mock_client_err, "token", user_info={})
    assert res4["_sync_errors"][0]["endpoint"] == "/api/error/"


def test_fetcher_for_each_edge_cases():
    mock_client = MagicMock()

    cfg = {
        "user_info_endpoints": [
            {
                "endpoint": "/api/items/{missing_key}/",
                "for_each": "items",
                "namespace": "results",
            }
        ]
    }
    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    res = fetcher.fetch(mock_client, "token", user_info={"items": [{"id": 1}]})
    assert res == {"items": [{"id": 1}], "results": []}

    mock_client_err = MagicMock()
    mock_client_err.get_endpoint_data.side_effect = Exception("Item fetch failed")

    cfg2 = {
        "user_info_endpoints": [
            {
                "endpoint": "/api/items/{id}/",
                "for_each": "items",
                "namespace": "results",
            }
        ]
    }
    fetcher2 = DefaultEndpointsUserInfoFetcher(suap_settings=cfg2)
    res2 = fetcher2.fetch(mock_client_err, "token", user_info={"items": [{"id": 1}]})
    assert res2["items"] == [{"id": 1}]
    assert res2["results"] == []
    assert "_sync_errors" in res2

    mock_client_dict = MagicMock()
    mock_client_dict.get_endpoint_data.return_value = {"detail": "info"}

    cfg3 = {
        "user_info_endpoints": [
            {
                "endpoint": "/api/items/{id}/",
                "for_each": "items",
                "namespace": "results",
            }
        ]
    }
    fetcher3 = DefaultEndpointsUserInfoFetcher(suap_settings=cfg3)
    res3 = fetcher3.fetch(mock_client_dict, "token", user_info={"items": [{"id": 1}]})
    assert res3["results"] == [{"detail": "info"}]


def test_fetcher_dict_endpoint_data_to_store():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.return_value = [1, 2, 3]

    cfg = {"user_info_endpoints": [{"endpoint": "/api/list/"}]}
    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    res = fetcher.fetch(mock_client, "token", user_info={})
    assert res == {}


def test_callable_target_in_fetcher_chain():
    def custom_fetcher(client_param, access_token, user_info=None):
        user_info = user_info or {}
        user_info["custom"] = True
        return user_info

    cfg = {"user_info_fetchers": [custom_fetcher]}
    fetchers = get_user_info_fetchers(cfg)
    assert fetchers == [custom_fetcher]

    result = run_user_info_fetcher_chain(None, "token", cfg=cfg)
    assert result == {"custom": True}


def test_fetcher_dict_spec_without_namespace_dict_store():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.side_effect = lambda token, path: {
        "/api/rh/eu/": {"identificacao": "2080882"},
        "/api/rh/detalhes/": {"cargo": "Professor", "campus": "CNAT"},
    }.get(path, {})

    cfg = {
        "user_info_endpoints": [
            "/api/rh/eu/",
            {
                "endpoint": "/api/rh/detalhes/",
            },
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-token")

    assert result["identificacao"] == "2080882"
    assert result["cargo"] == "Professor"
    assert result["campus"] == "CNAT"


# ---------------------------------------------------------------------------
# 4. JWT & Views Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "obtain_token_pair")
def test_token_pair_success(mock_obtain, client_fixture):
    mock_obtain.return_value = (
        200,
        {
            "access": "access_token_123",
            "refresh": "refresh_token_456",
            "username": "1234567",
        },
    )

    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({"username": "1234567", "password": "secretpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "access_token_123"
    assert data["refresh"] == "refresh_token_456"
    assert data["username"] == "1234567"
    mock_obtain.assert_called_once_with("1234567", "secretpassword")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "obtain_token_pair")
def test_token_pair_with_trailing_slash(mock_obtain, client_fixture):
    mock_obtain.return_value = (
        200,
        {
            "access": "access_token_123",
            "refresh": "refresh_token_456",
            "username": "1234567",
        },
    )

    response = client_fixture.post(
        "/api/token/pair/",
        data=json.dumps({"username": "1234567", "password": "secretpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"] == "access_token_123"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "obtain_token_pair")
def test_token_pair_invalid_credentials(mock_obtain, client_fixture):
    mock_obtain.return_value = (
        401,
        {
            "detail": "No active account found with the given credentials",
            "code": "authentication_failed",
        },
    )

    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({"username": "1234567", "password": "wrongpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "authentication_failed"


@pytest.mark.django_db
def test_token_pair_missing_fields(client_fixture):
    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({"password": "secretpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "username" in response.json()

    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({"username": "1234567"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "password" in response.json()

    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "username" in response.json()
    assert "password" in response.json()


@pytest.mark.django_db
def test_token_pair_invalid_types(client_fixture):
    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({"username": 12345, "password": ["not-a-string"]}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.json()
    assert "username" in data
    assert "password" in data


@pytest.mark.django_db
def test_token_pair_empty_and_invalid_body(client_fixture):
    response = client_fixture.post(
        "/api/token/pair",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Request body cannot be empty" in response.json()["detail"]

    response = client_fixture.post(
        "/api/token/pair",
        data="{invalid-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]

    response = client_fixture.post(
        "/api/token/pair",
        data="[1, 2, 3]",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "expected a JSON object" in response.json()["detail"]


@pytest.mark.django_db
def test_token_pair_method_not_allowed(client_fixture):
    response = client_fixture.get("/api/token/pair")
    assert response.status_code == 405
    assert response["Allow"] == "POST, OPTIONS"
    assert 'Method "GET" not allowed' in response.json()["detail"]


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "refresh_token")
def test_token_refresh_success(mock_refresh, client_fixture):
    mock_refresh.return_value = (
        200,
        {
            "access": "new_access_token",
            "refresh": "new_refresh_token",
        },
    )

    response = client_fixture.post(
        "/api/token/refresh",
        data=json.dumps({"refresh": "old_refresh_token"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "new_access_token"
    assert data["refresh"] == "new_refresh_token"
    mock_refresh.assert_called_once_with("old_refresh_token")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "refresh_token")
def test_token_refresh_with_trailing_slash(mock_refresh, client_fixture):
    mock_refresh.return_value = (
        200,
        {
            "access": "new_access_token",
            "refresh": "new_refresh_token",
        },
    )

    response = client_fixture.post(
        "/api/token/refresh/",
        data=json.dumps({"refresh": "old_refresh_token"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"] == "new_access_token"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "refresh_token")
def test_token_refresh_invalid_or_expired(mock_refresh, client_fixture):
    mock_refresh.return_value = (
        401,
        {
            "detail": "Token is invalid or expired",
            "code": "token_not_valid",
        },
    )

    response = client_fixture.post(
        "/api/token/refresh",
        data=json.dumps({"refresh": "invalid_refresh_token"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"


@pytest.mark.django_db
def test_token_refresh_missing_or_invalid_field(client_fixture):
    response = client_fixture.post(
        "/api/token/refresh",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "refresh" in response.json()

    response = client_fixture.post(
        "/api/token/refresh",
        data=json.dumps({"refresh": 12345}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "refresh" in response.json()

    response = client_fixture.post(
        "/api/token/refresh",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_token_refresh_method_not_allowed(client_fixture):
    response = client_fixture.get("/api/token/refresh")
    assert response.status_code == 405
    assert response["Allow"] == "POST, OPTIONS"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_success(mock_verify, client_fixture):
    mock_verify.return_value = (200, {})

    response = client_fixture.post(
        "/api/token/verify",
        data=json.dumps({"token": "valid_token_string"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {}
    mock_verify.assert_called_once_with("valid_token_string")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_with_trailing_slash(mock_verify, client_fixture):
    mock_verify.return_value = (200, {})

    response = client_fixture.post(
        "/api/token/verify/",
        data=json.dumps({"token": "valid_token_string"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_invalid(mock_verify, client_fixture):
    mock_verify.return_value = (
        401,
        {
            "detail": "Token is invalid or expired",
            "code": "token_not_valid",
        },
    )

    response = client_fixture.post(
        "/api/token/verify",
        data=json.dumps({"token": "expired_token_string"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"


@pytest.mark.django_db
def test_token_verify_missing_or_invalid_field(client_fixture):
    response = client_fixture.post(
        "/api/token/verify",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "token" in response.json()

    response = client_fixture.post(
        "/api/token/verify",
        data=json.dumps({"token": None}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "token" in response.json()

    response = client_fixture.post(
        "/api/token/verify",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_token_verify_method_not_allowed(client_fixture):
    response = client_fixture.get("/api/token/verify")
    assert response.status_code == 405
    assert response["Allow"] == "POST, OPTIONS"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "get_endpoint_data")
def test_user_info_fetch_success_bearer_header(mock_get_data, client_fixture):
    mock_get_data.return_value = {"identificacao": "2080882", "email": "kelson@ifrn.edu.br"}

    response = client_fixture.get(
        "/api/rh/eu/",
        HTTP_AUTHORIZATION="Bearer valid_jwt_access_token",
    )
    assert response.status_code == 200
    assert response.json()["identificacao"] == "2080882"
    mock_get_data.assert_called_once_with("valid_jwt_access_token", "/api/rh/eu/")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "get_endpoint_data")
def test_user_info_fetch_success_json_body(mock_get_data, client_fixture):
    mock_get_data.return_value = {"identificacao": "2080882", "email": "kelson@ifrn.edu.br"}

    response = client_fixture.post(
        "/api/token/user-info/",
        data=json.dumps({"token": "jwt_token_123", "endpoint": "/api/rh/eu/"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["identificacao"] == "2080882"
    mock_get_data.assert_called_once_with("jwt_token_123", "/api/rh/eu/")


@pytest.mark.django_db
def test_user_info_fetch_missing_token(client_fixture):
    response = client_fixture.get("/api/rh/eu/")
    assert response.status_code == 400
    assert "token" in response.json()


@pytest.mark.django_db
def test_user_info_fetch_method_not_allowed(client_fixture):
    response = client_fixture.delete("/api/rh/eu/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_user_info_fetch_invalid_json(client_fixture):
    response = client_fixture.post("/api/rh/eu/", data="invalid-json-body", content_type="application/json")
    assert response.status_code == 400
    assert "Invalid JSON" in response.json().get("detail", "")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "get_endpoint_data")
def test_user_info_fetch_query_params(mock_get_data, client_fixture):
    mock_get_data.return_value = {"dados": "ok"}
    response = client_fixture.get("/api/rh/eu/?token=query_tok&endpoint=/api/rh/meus-dados/")
    assert response.status_code == 200
    mock_get_data.assert_called_once_with("query_tok", "/api/rh/meus-dados/")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "get_endpoint_data")
def test_user_info_fetch_exception(mock_get_data, client_fixture):
    mock_get_data.side_effect = Exception("SUAP request failed")
    response = client_fixture.get("/api/rh/eu/", HTTP_AUTHORIZATION="Bearer valid_token")
    assert response.status_code == 400
    assert response.json() == {"detail": "SUAP request failed"}


def test_url_names_and_reversing():
    assert reverse("suap_jwt:pair") == "/api/token/pair"
    assert reverse("suap_jwt:refresh") == "/api/token/refresh"
    assert reverse("suap_jwt:verify") == "/api/token/verify"

    assert reverse("suap_api:token_pair") == "/api/token/pair"
    assert reverse("suap_api:token_refresh") == "/api/token/refresh"
    assert reverse("suap_api:token_verify") == "/api/token/verify"


def test_view_aliases():
    assert issubclass(SuapTokenPairView, BaseSuapTokenView)
    assert TokenObtainPairView is SuapTokenPairView
    assert SuapTokenObtainPairView is SuapTokenPairView
    assert TokenRefreshView is SuapTokenRefreshView
    assert TokenVerifyView is SuapTokenVerifyView
    assert SuapClient is SuapOAuth2Client


def test_client_jwt_methods():
    client_instance = SuapOAuth2Client(base_url="https://suap.example.com")

    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access": "a", "refresh": "r", "username": "myuser"}
        mock_post.return_value = mock_resp

        status, data = client_instance.obtain_token_pair("myuser", "mypass")
        assert status == 200
        assert data["username"] == "myuser"
        mock_post.assert_called_once_with(
            "https://suap.example.com/api/token/pair",
            json={"username": "myuser", "password": "mypass"},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access": "a2", "refresh": "r2"}
        mock_post.return_value = mock_resp

        status, data = client_instance.refresh_token("ref_token")
        assert status == 200
        assert data["access"] == "a2"

    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        status, data = client_instance.verify_token("acc_token")
        assert status == 200
        assert data == {}

    assert client_instance.post_token_pair == client_instance.obtain_token_pair
    assert client_instance.post_token_refresh == client_instance.refresh_token
    assert client_instance.post_token_verify == client_instance.verify_token


def test_client_post_json_endpoint_full_url():
    client_instance = SuapOAuth2Client(base_url="https://suap.example.com")

    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_resp

        status, data = client_instance._post_json_endpoint(
            "https://custom-suap.gov.br/api/token/pair",
            {"username": "u", "password": "p"},
        )
        assert status == 200
        assert data == {"status": "ok"}
        mock_post.assert_called_once_with(
            "https://custom-suap.gov.br/api/token/pair",
            json={"username": "u", "password": "p"},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )


def test_client_post_json_endpoint_non_json_response():
    client_instance = SuapOAuth2Client(base_url="https://suap.example.com")

    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.text = "Bad Gateway"
        mock_post.return_value = mock_resp

        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 502
        assert data == {"detail": "Bad Gateway"}

    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.text = ""
        mock_post.return_value = mock_resp

        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 204
        assert data == {}


def test_client_post_json_endpoint_network_exceptions():
    client_instance = SuapOAuth2Client(base_url="https://suap.example.com")

    with patch.object(client_instance._session, "post", side_effect=requests.Timeout("Connection timed out")):
        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 504
        assert "Gateway timeout" in data["detail"]

    with patch.object(client_instance._session, "post", side_effect=requests.ConnectionError("Connection refused")):
        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 503
        assert "SUAP service unavailable" in data["detail"]

    with patch.object(client_instance._session, "post", side_effect=RuntimeError("Unexpected")):
        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 500
        assert "Internal server error" in data["detail"]


def test_get_suap_settings_and_client_require_oauth_false(settings):
    settings.SUAP_AUTH = {
        "BASE_URL": "https://suap.ifrn.edu.br",
    }
    cfg = get_suap_settings(require_oauth=False)
    assert cfg["client_id"] == ""
    assert cfg["client_secret"] == ""
    assert cfg["redirect_uri"] == ""
    assert cfg["base_url"] == "https://suap.ifrn.edu.br"

    client_obj = get_oauth2_client(require_oauth=False)
    assert client_obj.base_url == "https://suap.ifrn.edu.br"
    assert client_obj.client_id == ""


@pytest.mark.django_db
def test_login_view_redirects_to_suap(client_fixture):
    response = client_fixture.get("/auth/suap/login/")
    assert response.status_code == 302
    assert "suap.ifrn.edu.br" in response["Location"]


@pytest.mark.django_db
def test_login_view_stores_state_in_session(client_fixture):
    response = client_fixture.get("/auth/suap/login/")
    assert response.status_code == 302
    assert "suap_oauth2_state" in client_fixture.session


@pytest.mark.django_db
def test_callback_view_handles_error_param(client_fixture):
    response = client_fixture.get("/auth/suap/callback/?error=access_denied")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
def test_callback_view_handles_state_mismatch(client_fixture):
    session = client_fixture.session
    session["suap_oauth2_state"] = "correct-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=abc&state=wrong-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_logs_in_user(mock_login, mock_auth, mock_get_client, client_fixture):
    User = get_user_model()
    user = User.objects.create_user(username="20211234567", email="joao@ifrn.edu.br")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok123"}
    mock_oauth.get_user_info.return_value = {
        "matricula": "20211234567",
        "nome_usual": "João Silva",
        "email": "joao@ifrn.edu.br",
    }
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = user

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=auth-code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"
    mock_login.assert_called_once()


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_handles_token_error(mock_get_client, client_fixture):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.side_effect = SuapTokenError("Token failed")
    mock_get_client.return_value = mock_oauth

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=bad-code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_authenticate_returns_none(mock_login, mock_auth, mock_get_client, client_fixture):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.return_value = {"matricula": "20211234567"}
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = None

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"
    mock_login.assert_not_called()


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_handles_user_info_error(mock_get_client, client_fixture):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.side_effect = SuapUserInfoError("Failed")
    mock_get_client.return_value = mock_oauth

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_redirects_to_safe_next_url(mock_login, mock_auth, mock_get_client, client_fixture):
    User = get_user_model()
    user = User.objects.create_user(username="20211234567", email="joao@ifrn.edu.br")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.return_value = {"matricula": "20211234567"}
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = user

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state&next=/dashboard/")
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_preserves_query_params_in_next(mock_login, mock_auth, mock_get_client, client_fixture):
    User = get_user_model()
    user = User.objects.create_user(username="20211234567", email="joao@ifrn.edu.br")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.return_value = {"matricula": "20211234567"}
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = user

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state&next=/dashboard/%3Ftab%3Dsettings")
    assert response.status_code == 302
    assert "/dashboard/" in response["Location"]


@pytest.mark.django_db
def test_login_view_intermediate_page(client_fixture, settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "DIRECT_REDIRECT": False,
    }
    response = client_fixture.get("/auth/suap/login/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_view_post_starts_oauth(client_fixture, settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "DIRECT_REDIRECT": False,
    }
    response = client_fixture.post("/auth/suap/login/")
    assert response.status_code == 302
    assert "suap.ifrn.edu.br" in response["Location"]


@pytest.mark.django_db
def test_login_view_renders_when_messages_exist(client_fixture, settings):
    settings.LOGIN_URL = "/auth/suap/login/"
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "DIRECT_REDIRECT": True,
    }
    response = client_fixture.get("/auth/suap/callback/?error=access_denied", follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_missing_access_token_in_token_response(mock_get_client, client_fixture):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {}  # No access_token
    mock_get_client.return_value = mock_oauth

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_token_exchange_generic_exception(mock_get_client, client_fixture):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.side_effect = Exception("Generic token error")
    mock_get_client.return_value = mock_oauth

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
def test_callback_view_handles_user_not_allowed_error(mock_auth, mock_get_client, client_fixture):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_get_client.return_value = mock_oauth
    mock_auth.side_effect = SuapUserNotAllowedError("User not allowed")

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_handles_unexpected_exception(mock_get_client, client_fixture):
    mock_get_client.side_effect = RuntimeError("Unexpected failure")

    session = client_fixture.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client_fixture.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


# ---------------------------------------------------------------------------
# 5. Mappers Tests
# ---------------------------------------------------------------------------


def test_mappers_resolve_callable():
    from django_suap_auth.mappers import resolve_callable as mappers_resolve_callable
    from django_suap_auth.mappers import resolve_callable_or_class as mappers_resolve_callable_or_class

    assert mappers_resolve_callable(format_cpf) is format_cpf
    assert mappers_resolve_callable("django_suap_auth.transformers.format_cpf") is format_cpf
    assert mappers_resolve_callable_or_class(format_cpf) is format_cpf
    with pytest.raises(TypeError):
        mappers_resolve_callable(12345)


def test_transformers_parse_date():
    assert parse_date("1995-01-15") == date(1995, 1, 15)
    assert parse_date(date(2020, 5, 20)) == date(2020, 5, 20)
    assert parse_date("invalid-date") is None
    assert parse_date("") is None


def test_transformers_format_cpf():
    assert format_cpf("12345678901") == "123.456.789-01"
    assert format_cpf("123.456.789-01") == "123.456.789-01"
    assert format_cpf("123") == "123"
    assert format_cpf("") == ""


def test_transformers_to_upper_and_lower():
    assert to_upper("teste") == "TESTE"
    assert to_lower("TESTE") == "teste"


def test_transformers_to_bool():
    assert to_bool(True) is True
    assert to_bool("sim") is True
    assert to_bool("1") is True
    assert to_bool("false") is False
    assert to_bool(0) is False


@patch("requests.get")
def test_transformers_fetch_image_file(mock_get):
    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_image_file("https://suap.ifrn.edu.br/media/fotos/75x100/12345.jpg")
    assert isinstance(result, ContentFile)
    assert result.read() == b"fake-image-bytes"
    assert result.name == "12345.jpg"


@patch("requests.get")
def test_transformers_fetch_image_file_failure(mock_get):
    mock_get.side_effect = Exception("Connection error")
    result = fetch_image_file("https://suap.ifrn.edu.br/media/foto.jpg")
    assert result is None


def test_mapper_lambda_and_callable_in_attr_map():
    info = {
        "identificacao": "20211234567",
        "primeiro_nome": "João",
        "ultimo_nome": "Silva",
        "tipo_vinculo": "Aluno",
    }
    attr_map = {
        "username": "identificacao",
        "full_name": lambda user_info: f"{user_info['primeiro_nome']} {user_info['ultimo_nome']}",
        "is_student": lambda user_info: user_info["tipo_vinculo"] == "Aluno",
    }
    mapper = DefaultSuapUserMapper()
    result = mapper.map_attributes(info, attr_map)

    assert result["username"] == "20211234567"
    assert result["full_name"] == "João Silva"
    assert result["is_student"] is True


def test_mapper_dict_spec_with_transformer_and_default():
    info = {
        "cpf": "12345678901",
        "data_nascimento": "1995-01-15",
        "url_foto_75x100": "https://suap.ifrn.edu.br/foto.jpg",
    }
    attr_map = {
        "cpf": {"key": "cpf", "transform": "django_suap_auth.transformers.format_cpf"},
        "data_nascimento": {"key": "data_nascimento", "transform": parse_date},
        "campus": {"key": "campus", "default": "Campus Central"},
    }
    mapper = DefaultSuapUserMapper()
    result = mapper.map_attributes(info, attr_map)

    assert result["cpf"] == "123.456.789-01"
    assert result["data_nascimento"] == date(1995, 1, 15)
    assert result["campus"] == "Campus Central"


class CustomTestUserMapper(BaseSuapUserMapper):
    def map_attributes(self, user_info, attr_map=None):
        res = super().map_attributes(user_info, attr_map)
        res["custom_flag"] = True
        return res


def test_custom_user_mapper_setting(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "USER_INFO_MAPPERS": [CustomTestUserMapper],
        "USER_ATTR_MAP": {"username": "identificacao"},
    }
    cfg = get_suap_settings()
    mapper = get_user_mapper(cfg)
    assert isinstance(mapper, CustomTestUserMapper)

    info = {"identificacao": "12345"}
    result = apply_user_attr_map(info, cfg["user_attr_map"], cfg=cfg)
    assert result["username"] == "12345"
    assert result["custom_flag"] is True


def test_extract_nested_invalid_key():
    assert _extract_nested({"a": 1}, 12345) is None


def test_call_transformer_signatures():
    def func3(a, b, c=None):
        return f"{a}-{b}-{c}"

    assert _call_transformer(func3, "val", "info") == "val-info-None"

    def func3_strict(a, b, c):
        return f"{a}-{b}-{c}"

    with pytest.raises(TypeError):
        _call_transformer(func3_strict, "val", "info")


def test_mapper_dict_spec_missing_key_no_default_no_transform():
    mapper = BaseUserMapper()
    user_info = {"other": "val"}
    attr_map = {"field": {"key": "missing"}}
    res = mapper.map_attributes(user_info, attr_map)
    assert "field" not in res


def test_base_user_mapper_map_attributes_none():
    mapper = BaseUserMapper()
    assert mapper.map_attributes({"a": 1}) == {}


def test_get_user_info_mappers_default_cfg():
    mappers = get_user_info_mappers()
    assert len(mappers) >= 1
    assert isinstance(mappers[0], DefaultAttrMapUserMapper)


def test_callable_target_in_mapper_chain():
    def custom_mapper(user_info, attr_map=None):
        return {"custom_attr": "mapped"}

    cfg = {"user_info_mappers": [custom_mapper]}
    mappers = get_user_info_mappers(cfg)
    assert mappers == [custom_mapper]

    result = run_user_info_mapper_chain({"user": "info"}, cfg=cfg)
    assert result == {"custom_attr": "mapped"}


def test_to_bool_fallback():
    class CustomObj:
        def __bool__(self):
            return True

    assert to_bool(CustomObj()) is True


def test_fetch_image_file_edge_cases():
    assert fetch_image_file(12345) is None
    assert fetch_image_file("") is None


@responses.activate
def test_fetch_image_file_no_extension():
    responses.add(
        responses.GET,
        "https://suap.ifrn.edu.br/media/foto",
        body=b"fake-image-bytes",
        status=200,
    )
    file_obj = fetch_image_file("https://suap.ifrn.edu.br/media/foto")
    assert file_obj is not None
    assert file_obj.name == "foto.jpg"


# ---------------------------------------------------------------------------
# 6. Utils & Exceptions Tests
# ---------------------------------------------------------------------------


def test_get_suap_settings_returns_dict():
    cfg = get_suap_settings()
    assert cfg["client_id"] == "test-client-id"
    assert cfg["client_secret"] == "test-client-secret"
    assert cfg["redirect_uri"] == "http://localhost:8000/auth/suap/callback/"
    assert cfg["scopes"] == ["identificacao", "email"]
    assert cfg["base_url"] == "https://suap.ifrn.edu.br"
    assert cfg["user_lookup_field"] == "username"
    assert cfg["direct_redirect"] is True


def test_get_suap_settings_raises_on_missing_client_id(settings):
    settings.SUAP_AUTH = {
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
    }
    with pytest.raises(ImproperlyConfigured):
        get_suap_settings()


def test_get_suap_settings_raises_on_missing_secret(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "REDIRECT_URI": "http://localhost/callback/",
    }
    with pytest.raises(ImproperlyConfigured):
        get_suap_settings()


def test_get_suap_settings_raises_on_missing_redirect_uri(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
    }
    with pytest.raises(ImproperlyConfigured):
        get_suap_settings()


def test_generate_state_returns_string():
    state = generate_state()
    assert isinstance(state, str)
    assert len(state) > 20


def test_generate_state_is_unique():
    states = {generate_state() for _ in range(10)}
    assert len(states) == 10


def test_apply_user_attr_map_simple_fields():
    info = {"matricula": "20211234567", "email": "joao@academico.ifrn.edu.br"}
    result = apply_user_attr_map(info, {"username": "matricula", "email": "email"})
    assert result == {"username": "20211234567", "email": "joao@academico.ifrn.edu.br"}


def test_apply_user_attr_map_name_split():
    info = {"nome_registro": "João Silva Santos"}
    result = apply_user_attr_map(info, {("first_name", "last_name"): "nome_registro"})
    assert result["first_name"] == "João Silva"
    assert result["last_name"] == "Santos"


def test_apply_user_attr_map_name_single_word():
    info = {"nome_usual": "Cher"}
    result = apply_user_attr_map(info, {("first_name", "last_name"): "nome_usual"})
    assert result["first_name"] == "Cher"
    assert result["last_name"] == ""


def test_apply_user_attr_map_name_to_single_field():
    info = {"nome_usual": "Maria Silva"}
    result = apply_user_attr_map(info, {"nome_completo": "nome_usual"})
    assert result["nome_completo"] == "Maria Silva"


def test_apply_user_attr_map_nested_dotted_key():
    info = {"dados_pessoais": {"data_nascimento": "1995-01-15", "cpf": "12345678901"}}
    result = apply_user_attr_map(
        info,
        {
            "data_nascimento": "dados_pessoais.data_nascimento",
            "cpf": "dados_pessoais.cpf",
        },
    )
    assert result["data_nascimento"] == "1995-01-15"
    assert result["cpf"] == "12345678901"


def test_apply_user_attr_map_fulljson():
    info = {"matricula": "20211234567", "email": "joao@ifrn.edu.br"}
    result = apply_user_attr_map(info, {"perfil_json": "fulljson"})
    assert result["perfil_json"] is info


def test_apply_user_attr_map_skips_missing_keys():
    info = {"matricula": "20211234567"}
    result = apply_user_attr_map(info, {"username": "matricula", "email": "email"})
    assert "email" not in result


def test_apply_user_attr_map_skips_none_values():
    info = {"matricula": None}
    result = apply_user_attr_map(info, {"username": "matricula"})
    assert "username" not in result


def test_extract_nested_non_dict_mid_path():
    from django_suap_auth.utils import _extract_nested

    info = {"dados_pessoais": "not_a_dict"}
    assert _extract_nested(info, "dados_pessoais.data_nascimento") is None


def test_get_oauth2_client_returns_client():
    client_obj = get_oauth2_client()
    assert isinstance(client_obj, SuapOAuth2Client)


def test_suap_api_error_with_status_code():
    error = SuapAPIError("API Error", status_code=400)
    assert error.status_code == 400
    assert str(error) == "API Error"


def test_suap_token_error():
    error = SuapTokenError("Token exchange failed")
    assert str(error) == "Token exchange failed"


def test_suap_user_info_error():
    error = SuapUserInfoError("Failed to fetch user info")
    assert str(error) == "Failed to fetch user info"


def test_suap_state_mismatch_error():
    error = SuapStateMismatchError("State mismatch - possible CSRF")
    assert str(error) == "State mismatch - possible CSRF"


def test_get_suap_settings_legacy_user_mapper(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "id",
        "CLIENT_SECRET": "sec",
        "REDIRECT_URI": "http://localhost/callback/",
        "USER_MAPPER": "django_suap_auth.mappers.DefaultAttrMapUserMapper",
    }
    cfg = get_suap_settings()
    assert cfg["user_info_mappers"] == ["django_suap_auth.mappers.DefaultAttrMapUserMapper"]


def test_suap_auth_templatetags(settings):
    from django_suap_auth.templatetags.suap_auth import suap_base_url, suap_login_url

    settings.SUAP_AUTH = {
        "CLIENT_ID": "id",
        "CLIENT_SECRET": "sec",
        "REDIRECT_URI": "http://localhost/callback/",
        "BASE_URL": "https://suap.custom.edu.br/",
    }
    assert suap_base_url() == "https://suap.custom.edu.br"
    assert suap_login_url() == "https://suap.custom.edu.br/accounts/login/"


def test_logged_out_template_rendering(settings):
    from django.template.loader import render_to_string

    settings.SUAP_AUTH = {
        "CLIENT_ID": "id",
        "CLIENT_SECRET": "sec",
        "REDIRECT_URI": "http://localhost/callback/",
        "BASE_URL": "https://suap.test.edu.br",
    }
    html = render_to_string("registration/logged_out.html")
    assert "Sessão Encerrada" in html
    assert "Você fez logout apenas na sessão desta aplicação" in html
    assert "SUAP não possui um mecanismo de fazer logout seguro em TODAS as aplicações" in html
    assert "1. Fazer logout no SUAP e depois fechar a janela" in html
    assert "2. Fechar a janela manualmente" in html
    assert "3. Voltar a fazer login na aplicação" in html
    assert "4. Seguir como está" in html
    assert "https://suap.test.edu.br/accounts/login/" in html

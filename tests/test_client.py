import pytest
import responses as responses_lib

from django_suap_auth.client import AVAILABLE_SCOPES, SuapOAuth2Client
from django_suap_auth.exceptions import SuapTokenError, SuapUserInfoError


def make_client(**kwargs):
    return SuapOAuth2Client(
        client_id="test-client-id",
        client_secret="test-secret",
        redirect_uri="http://localhost/callback/",
        **kwargs,
    )


def test_client_defaults():
    client = make_client()
    assert client.base_url == "https://suap.ifrn.edu.br"
    assert client.scopes == ["identificacao", "email"]


def test_client_custom_base_url():
    client = make_client(base_url="https://suap.example.com/")
    assert client.base_url == "https://suap.example.com"


def test_client_custom_scopes():
    client = make_client(scopes=["identificacao", "email", "dados_academicos"])
    assert "dados_academicos" in client.scopes


def test_available_scopes_list():
    assert "identificacao" in AVAILABLE_SCOPES
    assert "email" in AVAILABLE_SCOPES
    assert "documentos_pessoais" in AVAILABLE_SCOPES
    assert "dados_academicos" in AVAILABLE_SCOPES
    assert "dados_pessoais" in AVAILABLE_SCOPES
    assert "reitoria" in AVAILABLE_SCOPES


def test_get_authorization_url_contains_required_params():
    client = make_client()
    url = client.get_authorization_url("test-state-123")
    assert "response_type=code" in url
    assert "client_id=test-client-id" in url
    assert "state=test-state-123" in url
    assert "suap.ifrn.edu.br" in url


def test_get_authorization_url_contains_scopes():
    client = make_client(scopes=["identificacao", "email"])
    url = client.get_authorization_url("state")
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
    client = make_client()
    result = client.exchange_code_for_token("auth-code-xyz")
    assert result["access_token"] == "abc123"


@responses_lib.activate
def test_exchange_code_for_token_http_error():
    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        json={"error": "invalid_grant"},
        status=400,
    )
    client = make_client()
    with pytest.raises(SuapTokenError):
        client.exchange_code_for_token("bad-code")


@responses_lib.activate
def test_exchange_code_for_token_connection_error():
    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        body=Exception("connection refused"),
    )
    client = make_client()
    with pytest.raises(SuapTokenError):
        client.exchange_code_for_token("code")


@responses_lib.activate
def test_get_user_info_success():
    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        json={"identificacao": "20211234567", "nome_usual": "João Silva", "email": "joao@ifrn.edu.br"},
        status=200,
    )
    client = make_client()
    result = client.get_user_info("access-token-xyz")
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
    client = make_client()
    with pytest.raises(SuapUserInfoError):
        client.get_user_info("bad-token")


@responses_lib.activate
def test_get_user_info_connection_error():
    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        body=Exception("connection refused"),
    )
    client = make_client()
    with pytest.raises(SuapUserInfoError):
        client.get_user_info("token")


@responses_lib.activate
def test_exchange_code_request_exception():
    """Test RequestException (not HTTPError) during token exchange"""
    import requests

    responses_lib.add(
        responses_lib.POST,
        "https://suap.ifrn.edu.br/o/token/",
        body=requests.Timeout("timeout"),
    )
    client = make_client()
    with pytest.raises(SuapTokenError):
        client.exchange_code_for_token("auth-code")


@responses_lib.activate
def test_get_user_info_request_exception():
    """Test RequestException (not HTTPError) during user info fetch"""
    import requests

    responses_lib.add(
        responses_lib.GET,
        "https://suap.ifrn.edu.br/api/rh/eu/",
        body=requests.ConnectionError("connection error"),
    )
    client = make_client()
    with pytest.raises(SuapUserInfoError):
        client.get_user_info("token")

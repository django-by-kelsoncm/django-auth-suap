import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.test import Client
from django.urls import reverse

from django_suap_auth.client import SuapClient, SuapOAuth2Client
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
from django_suap_auth.utils import get_oauth2_client, get_suap_settings


@pytest.fixture
def client():
    return Client()


# ---------------------------------------------------------------------------
# SuapTokenPairView tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "obtain_token_pair")
def test_token_pair_success(mock_obtain, client):
    mock_obtain.return_value = (
        200,
        {
            "access": "access_token_123",
            "refresh": "refresh_token_456",
            "username": "1234567",
        },
    )

    response = client.post(
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
def test_token_pair_with_trailing_slash(mock_obtain, client):
    mock_obtain.return_value = (
        200,
        {
            "access": "access_token_123",
            "refresh": "refresh_token_456",
            "username": "1234567",
        },
    )

    response = client.post(
        "/api/token/pair/",
        data=json.dumps({"username": "1234567", "password": "secretpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"] == "access_token_123"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "obtain_token_pair")
def test_token_pair_invalid_credentials(mock_obtain, client):
    mock_obtain.return_value = (
        401,
        {
            "detail": "No active account found with the given credentials",
            "code": "authentication_failed",
        },
    )

    response = client.post(
        "/api/token/pair",
        data=json.dumps({"username": "1234567", "password": "wrongpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "authentication_failed"


@pytest.mark.django_db
def test_token_pair_missing_fields(client):
    # Missing username
    response = client.post(
        "/api/token/pair",
        data=json.dumps({"password": "secretpassword"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "username" in response.json()

    # Missing password
    response = client.post(
        "/api/token/pair",
        data=json.dumps({"username": "1234567"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "password" in response.json()

    # Missing both
    response = client.post(
        "/api/token/pair",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "username" in response.json()
    assert "password" in response.json()


@pytest.mark.django_db
def test_token_pair_invalid_types(client):
    response = client.post(
        "/api/token/pair",
        data=json.dumps({"username": 12345, "password": ["not-a-string"]}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.json()
    assert "username" in data
    assert "password" in data


@pytest.mark.django_db
def test_token_pair_empty_and_invalid_body(client):
    # Empty body
    response = client.post(
        "/api/token/pair",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Request body cannot be empty" in response.json()["detail"]

    # Invalid JSON
    response = client.post(
        "/api/token/pair",
        data="{invalid-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]

    # Non-dict JSON (array)
    response = client.post(
        "/api/token/pair",
        data="[1, 2, 3]",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "expected a JSON object" in response.json()["detail"]


@pytest.mark.django_db
def test_token_pair_method_not_allowed(client):
    response = client.get("/api/token/pair")
    assert response.status_code == 405
    assert response["Allow"] == "POST, OPTIONS"
    assert 'Method "GET" not allowed' in response.json()["detail"]


# ---------------------------------------------------------------------------
# SuapTokenRefreshView tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "refresh_token")
def test_token_refresh_success(mock_refresh, client):
    mock_refresh.return_value = (
        200,
        {
            "access": "new_access_token",
            "refresh": "new_refresh_token",
        },
    )

    response = client.post(
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
def test_token_refresh_with_trailing_slash(mock_refresh, client):
    mock_refresh.return_value = (
        200,
        {
            "access": "new_access_token",
            "refresh": "new_refresh_token",
        },
    )

    response = client.post(
        "/api/token/refresh/",
        data=json.dumps({"refresh": "old_refresh_token"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"] == "new_access_token"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "refresh_token")
def test_token_refresh_invalid_or_expired(mock_refresh, client):
    mock_refresh.return_value = (
        401,
        {
            "detail": "Token is invalid or expired",
            "code": "token_not_valid",
        },
    )

    response = client.post(
        "/api/token/refresh",
        data=json.dumps({"refresh": "invalid_refresh_token"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"


@pytest.mark.django_db
def test_token_refresh_missing_or_invalid_field(client):
    # Missing refresh
    response = client.post(
        "/api/token/refresh",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "refresh" in response.json()

    # Invalid type
    response = client.post(
        "/api/token/refresh",
        data=json.dumps({"refresh": 12345}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "refresh" in response.json()

    # Empty body
    response = client.post(
        "/api/token/refresh",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_token_refresh_method_not_allowed(client):
    response = client.get("/api/token/refresh")
    assert response.status_code == 405
    assert response["Allow"] == "POST, OPTIONS"


# ---------------------------------------------------------------------------
# SuapTokenVerifyView tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_success(mock_verify, client):
    mock_verify.return_value = (200, {})

    response = client.post(
        "/api/token/verify",
        data=json.dumps({"token": "valid_token_string"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {}
    mock_verify.assert_called_once_with("valid_token_string")


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_with_trailing_slash(mock_verify, client):
    mock_verify.return_value = (200, {})

    response = client.post(
        "/api/token/verify/",
        data=json.dumps({"token": "valid_token_string"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_invalid(mock_verify, client):
    mock_verify.return_value = (
        401,
        {
            "detail": "Token is invalid or expired",
            "code": "token_not_valid",
        },
    )

    response = client.post(
        "/api/token/verify",
        data=json.dumps({"token": "expired_token_string"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"


@pytest.mark.django_db
def test_token_verify_missing_or_invalid_field(client):
    # Missing token
    response = client.post(
        "/api/token/verify",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "token" in response.json()

    # Invalid type
    response = client.post(
        "/api/token/verify",
        data=json.dumps({"token": None}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "token" in response.json()

    # Empty body
    response = client.post(
        "/api/token/verify",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_token_verify_method_not_allowed(client):
    response = client.get("/api/token/verify")
    assert response.status_code == 405
    assert response["Allow"] == "POST, OPTIONS"


# ---------------------------------------------------------------------------
# URL reversing and view aliases tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Client JWT methods & edge cases
# ---------------------------------------------------------------------------


def test_client_jwt_methods():
    client_instance = SuapOAuth2Client(base_url="https://suap.example.com")

    # obtain_token_pair
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

    # refresh_token
    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access": "a2", "refresh": "r2"}
        mock_post.return_value = mock_resp

        status, data = client_instance.refresh_token("ref_token")
        assert status == 200
        assert data["access"] == "a2"

    # verify_token
    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        status, data = client_instance.verify_token("acc_token")
        assert status == 200
        assert data == {}

    # aliases
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

    # HTML text response
    with patch.object(client_instance._session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.text = "Bad Gateway"
        mock_post.return_value = mock_resp

        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 502
        assert data == {"detail": "Bad Gateway"}

    # Empty text response
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

    # Timeout
    with patch.object(client_instance._session, "post", side_effect=requests.Timeout("Connection timed out")):
        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 504
        assert "Gateway timeout" in data["detail"]

    # RequestException
    with patch.object(client_instance._session, "post", side_effect=requests.ConnectionError("Connection refused")):
        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 503
        assert "SUAP service unavailable" in data["detail"]

    # Generic Exception
    with patch.object(client_instance._session, "post", side_effect=RuntimeError("Unexpected")):
        status, data = client_instance._post_json_endpoint("/api/token/pair", {})
        assert status == 500
        assert "Internal server error" in data["detail"]


def test_get_suap_settings_and_client_require_oauth_false(settings):
    # Only BASE_URL configured (no CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    settings.SUAP_AUTH = {
        "BASE_URL": "https://suap.ifrn.edu.br",
    }
    cfg = get_suap_settings(require_oauth=False)
    assert cfg["client_id"] == ""
    assert cfg["client_secret"] == ""
    assert cfg["redirect_uri"] == ""
    assert cfg["base_url"] == "https://suap.ifrn.edu.br"

    client = get_oauth2_client(require_oauth=False)
    assert client.base_url == "https://suap.ifrn.edu.br"
    assert client.client_id == ""

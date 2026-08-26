import json
from unittest.mock import patch

import pytest
from django.apps import apps
from django.test import Client
from django.urls import reverse

from django_suap_auth.client import SuapOAuth2Client
from django_suap_auth.jwt.apps import SuapAuthJwtConfig
from django_suap_auth.jwt.views import (
    BaseSuapTokenView,
    SuapApiFetchView,
    SuapTokenObtainPairView,
    SuapTokenPairView,
    SuapTokenRefreshView,
    SuapTokenVerifyView,
    SuapUserInfoFetchView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


@pytest.fixture
def client_fixture():
    return Client()


def test_apps_config():
    assert SuapAuthJwtConfig.name == "django_suap_auth.jwt"
    assert SuapAuthJwtConfig.label == "django_suap_auth_jwt"
    assert SuapAuthJwtConfig.verbose_name == "SUAP Auth JWT"
    app_config = apps.get_app_config("django_suap_auth_jwt")
    assert isinstance(app_config, SuapAuthJwtConfig)


def test_view_aliases():
    assert issubclass(SuapTokenPairView, BaseSuapTokenView)
    assert TokenObtainPairView is SuapTokenPairView
    assert SuapTokenObtainPairView is SuapTokenPairView
    assert TokenRefreshView is SuapTokenRefreshView
    assert TokenVerifyView is SuapTokenVerifyView
    assert SuapApiFetchView is SuapUserInfoFetchView


def test_url_reversing():
    assert reverse("suap_jwt:pair") == "/api/token/pair"
    assert reverse("suap_jwt:refresh") == "/api/token/refresh"
    assert reverse("suap_jwt:verify") == "/api/token/verify"
    assert reverse("suap_jwt:user_info") == "/api/token/user-info"
    assert reverse("suap_jwt:rh_eu") == "/api/token/rh/eu"


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "obtain_token_pair")
def test_token_pair_success(mock_obtain, client_fixture):
    mock_obtain.return_value = (200, {"access": "acc", "refresh": "ref", "username": "user1"})
    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({"username": "user1", "password": "pass1"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"] == "acc"
    mock_obtain.assert_called_once_with("user1", "pass1")


@pytest.mark.django_db
def test_token_pair_missing_fields(client_fixture):
    response = client_fixture.post(
        "/api/token/pair",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "username" in response.json()
    assert "password" in response.json()


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "refresh_token")
def test_token_refresh_success(mock_refresh, client_fixture):
    mock_refresh.return_value = (200, {"access": "acc2", "refresh": "ref2"})
    response = client_fixture.post(
        "/api/token/refresh",
        data=json.dumps({"refresh": "ref1"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["access"] == "acc2"
    mock_refresh.assert_called_once_with("ref1")


@pytest.mark.django_db
def test_token_refresh_missing_field(client_fixture):
    response = client_fixture.post(
        "/api/token/refresh",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "refresh" in response.json()


@pytest.mark.django_db
@patch.object(SuapOAuth2Client, "verify_token")
def test_token_verify_success(mock_verify, client_fixture):
    mock_verify.return_value = (200, {})
    response = client_fixture.post(
        "/api/token/verify",
        data=json.dumps({"token": "acc"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {}
    mock_verify.assert_called_once_with("acc")


@pytest.mark.django_db
def test_token_verify_missing_field(client_fixture):
    response = client_fixture.post(
        "/api/token/verify",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "token" in response.json()

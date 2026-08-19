from unittest.mock import MagicMock, patch

import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_login_view_redirects_to_suap(client):
    response = client.get("/auth/suap/login/")
    assert response.status_code == 302
    assert "suap.ifrn.edu.br" in response["Location"]


@pytest.mark.django_db
def test_login_view_stores_state_in_session(client):
    response = client.get("/auth/suap/login/")
    assert response.status_code == 302
    assert "suap_oauth2_state" in client.session


@pytest.mark.django_db
def test_callback_view_handles_error_param(client):
    response = client.get("/auth/suap/callback/?error=access_denied")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
def test_callback_view_handles_state_mismatch(client):
    session = client.session
    session["suap_oauth2_state"] = "correct-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=abc&state=wrong-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_logs_in_user(mock_login, mock_auth, mock_get_client, client):
    from django.contrib.auth import get_user_model

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

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=auth-code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"
    mock_login.assert_called_once()


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_handles_token_error(mock_get_client, client):
    from django_suap_auth.exceptions import SuapTokenError

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.side_effect = SuapTokenError("Token failed")
    mock_get_client.return_value = mock_oauth

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=bad-code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_authenticate_returns_none(mock_login, mock_auth, mock_get_client, client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.return_value = {"matricula": "20211234567"}
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = None

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"
    mock_login.assert_not_called()


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_handles_user_info_error(mock_get_client, client):
    from django_suap_auth.exceptions import SuapUserInfoError

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.side_effect = SuapUserInfoError("Failed")
    mock_get_client.return_value = mock_oauth

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_redirects_to_safe_next_url(mock_login, mock_auth, mock_get_client, client):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(username="20211234567", email="joao@ifrn.edu.br")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.return_value = {"matricula": "20211234567"}
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = user

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state&next=/dashboard/")
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
@patch("django_suap_auth.views.authenticate")
@patch("django_suap_auth.views.login")
def test_callback_view_preserves_query_params_in_next(mock_login, mock_auth, mock_get_client, client):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(username="20211234567", email="joao@ifrn.edu.br")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_oauth.get_user_info.return_value = {"matricula": "20211234567"}
    mock_get_client.return_value = mock_oauth
    mock_auth.return_value = user

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state&next=/dashboard/%3Ftab%3Dsettings")
    assert response.status_code == 302
    assert "/dashboard/" in response["Location"]


@pytest.mark.django_db
def test_login_view_intermediate_page(client, settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "DIRECT_REDIRECT": False,
    }
    response = client.get("/auth/suap/login/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_view_post_starts_oauth(client, settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "DIRECT_REDIRECT": False,
    }
    response = client.post("/auth/suap/login/")
    assert response.status_code == 302
    assert "suap.ifrn.edu.br" in response["Location"]


@pytest.mark.django_db
def test_login_view_renders_when_messages_exist(client, settings):
    settings.LOGIN_URL = "/auth/suap/login/"
    settings.SUAP_AUTH = {
        "CLIENT_ID": "test-id",
        "CLIENT_SECRET": "test-secret",
        "REDIRECT_URI": "http://localhost/callback/",
        "DIRECT_REDIRECT": True,
    }
    # Simulate a callback error setting a message
    response = client.get("/auth/suap/callback/?error=access_denied", follow=True)
    # The callback view redirects to LOGIN_URL (/auth/suap/login/) with message.
    # It should render 200 (intermediate template) instead of 302 looping redirect to SUAP.
    assert response.status_code == 200

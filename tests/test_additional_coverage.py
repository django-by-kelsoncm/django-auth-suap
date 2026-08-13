from unittest.mock import MagicMock, patch

import pytest
import responses
from django.contrib.auth import get_user_model

from django_suap_auth.backends import SuapAuthBackend, _filter_fields
from django_suap_auth.client import SuapOAuth2Client
from django_suap_auth.exceptions import SuapUserNotAllowedError
from django_suap_auth.fetchers import (
    BaseUserInfoFetcher,
    DefaultEndpointsUserInfoFetcher,
    get_user_info_fetchers,
    run_user_info_fetcher_chain,
)
from django_suap_auth.mappers import (
    BaseUserMapper,
    DefaultAttrMapUserMapper,
    _call_transformer,
    _extract_nested,
    get_user_info_mappers,
    run_user_info_mapper_chain,
)
from django_suap_auth.transformers import fetch_image_file, to_bool
from django_suap_auth.utils import get_suap_settings


# ----------------------------------------------------------------------
# 1. Backends coverage
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# 2. Client coverage
# ----------------------------------------------------------------------
@responses.activate
def test_client_get_endpoint_data_full_url():
    client = SuapOAuth2Client(
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
    data = client.get_endpoint_data("token", "https://suap.ifrn.edu.br/api/rh/eu/")
    assert data["identificacao"] == "123"


# ----------------------------------------------------------------------
# 3. Fetchers coverage
# ----------------------------------------------------------------------
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
    assert res4 == {}


def test_fetcher_for_each_edge_cases():
    # Item formatting error
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

    # Exception during for_each item fetch
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
    assert res2 == {"items": [{"id": 1}], "results": []}

    # for_each item returning dict (non-list extracted)
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
    # data_to_store is list or non-dict without namespace
    mock_client = MagicMock()
    mock_client.get_endpoint_data.return_value = [1, 2, 3]

    cfg = {"user_info_endpoints": [{"endpoint": "/api/list/"}]}
    fetcher = DefaultEndpointsUserInfoFetcher(suap_settings=cfg)
    res = fetcher.fetch(mock_client, "token", user_info={})
    assert res == {}


def test_callable_target_in_fetcher_chain():
    def custom_fetcher(client, access_token, user_info=None):
        user_info = user_info or {}
        user_info["custom"] = True
        return user_info

    cfg = {"user_info_fetchers": [custom_fetcher]}
    fetchers = get_user_info_fetchers(cfg)
    assert fetchers == [custom_fetcher]

    result = run_user_info_fetcher_chain(None, "token", cfg=cfg)
    assert result == {"custom": True}


# ----------------------------------------------------------------------
# 4. Mappers coverage
# ----------------------------------------------------------------------
def test_extract_nested_invalid_key():
    assert _extract_nested({"a": 1}, 12345) is None


def test_call_transformer_signatures():
    # 3-parameter function with default
    def func3(a, b, c=None):
        return f"{a}-{b}-{c}"

    assert _call_transformer(func3, "val", "info") == "val-info-None"

    # Function expecting 3 positional args (raises TypeError on 2 args and 1 arg)
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


# ----------------------------------------------------------------------
# 5. Transformers coverage
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# 6. Utils coverage
# ----------------------------------------------------------------------
def test_get_suap_settings_legacy_user_mapper(settings):
    settings.SUAP_AUTH = {
        "CLIENT_ID": "id",
        "CLIENT_SECRET": "sec",
        "REDIRECT_URI": "http://localhost/callback/",
        "USER_MAPPER": "django_suap_auth.mappers.DefaultAttrMapUserMapper",
    }
    cfg = get_suap_settings()
    assert cfg["user_info_mappers"] == ["django_suap_auth.mappers.DefaultAttrMapUserMapper"]


# ----------------------------------------------------------------------
# 7. Views coverage
# ----------------------------------------------------------------------
@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_missing_access_token_in_token_response(mock_get_client, client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {}  # No access_token
    mock_get_client.return_value = mock_oauth

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_token_exchange_generic_exception(mock_get_client, client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.side_effect = Exception("Generic token error")
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
def test_callback_view_handles_user_not_allowed_error(mock_auth, mock_get_client, client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "tok"}
    mock_get_client.return_value = mock_oauth
    mock_auth.side_effect = SuapUserNotAllowedError("User not allowed")

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"


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


@pytest.mark.django_db
@patch("django_suap_auth.views.get_oauth2_client")
def test_callback_view_handles_unexpected_exception(mock_get_client, client):
    mock_get_client.side_effect = RuntimeError("Unexpected failure")

    session = client.session
    session["suap_oauth2_state"] = "valid-state"
    session.save()

    response = client.get("/auth/suap/callback/?code=code&state=valid-state")
    assert response.status_code == 302
    assert response["Location"] == "/login/"

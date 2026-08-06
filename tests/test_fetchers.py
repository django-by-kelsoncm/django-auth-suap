from unittest.mock import MagicMock

import pytest

from django_suap_auth.fetchers import (
    BaseUserInfoFetcher,
    DefaultEndpointsUserInfoFetcher,
    resolve_callable,
    resolve_callable_or_class,
    run_user_info_fetcher_chain,
)
from django_suap_auth.utils import get_suap_settings


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



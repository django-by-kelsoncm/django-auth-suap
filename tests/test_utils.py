import pytest
from django.core.exceptions import ImproperlyConfigured

from django_suap_auth.utils import apply_user_attr_map, generate_state, get_suap_settings


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
    from django_suap_auth.client import SuapOAuth2Client
    from django_suap_auth.utils import get_oauth2_client

    client = get_oauth2_client()
    assert isinstance(client, SuapOAuth2Client)


# Tests para exceções e casos adicionais
def test_suap_api_error_with_status_code():
    from django_suap_auth.exceptions import SuapAPIError

    error = SuapAPIError("API Error", status_code=400)
    assert error.status_code == 400
    assert str(error) == "API Error"


def test_suap_token_error():
    from django_suap_auth.exceptions import SuapTokenError

    error = SuapTokenError("Token exchange failed")
    assert str(error) == "Token exchange failed"


def test_suap_user_info_error():
    from django_suap_auth.exceptions import SuapUserInfoError

    error = SuapUserInfoError("Failed to fetch user info")
    assert str(error) == "Failed to fetch user info"


def test_suap_state_mismatch_error():
    from django_suap_auth.exceptions import SuapStateMismatchError

    error = SuapStateMismatchError("State mismatch - possible CSRF")
    assert str(error) == "State mismatch - possible CSRF"

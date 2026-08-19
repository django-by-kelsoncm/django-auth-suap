import pytest
from django.contrib.auth import get_user_model

from django_suap_auth.backends import SuapAuthBackend


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

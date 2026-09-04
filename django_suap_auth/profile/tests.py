from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from django_suap_auth.profile.backends import SuapProfileAuthBackend, sync_suap_profile

User = get_user_model()


@pytest.mark.django_db
def test_sync_suap_profile_servidor():
    user = User.objects.create_user(username="2080882", email="servidor@ifrn.edu.br")
    raw_info = {
        "id": 100,
        "identificacao": "2080882",
        "nome_usual": "Kelson Medeiros",
        "cpf": "111.222.333-44",
        "rg": "123456 SSP/RN",
        "filiacao": ["Mae", "Pai"],
        "data_nascimento": "1980-05-15",
        "naturalidade": "Natal/RN",
        "tipo_sanguineo": "O+",
        "sexo": "M",
        "tipo_vinculo": "Servidor",
        "tipo_usuario": "Servidor (Docente)",
        "categoria": "Docente",
        "cargo": "Professor EBTT",
        "setor_suap": "DEAD/ZL",
        "campus": "ZL",
        "meus_vinculos": [
            {
                "id": 1,
                "identificador": "2080882",
                "tipo": "servidor",
                "campus": "ZL",
                "cargo": "Professor",
                "categoria": "Docente",
                "ativo": True,
            }
        ],
    }

    perfil = sync_suap_profile(user, raw_info)

    assert perfil is not None
    assert perfil.user == user
    assert perfil.matricula == "2080882"
    assert perfil.cpf == "11122233344"
    assert perfil.nome_usual == "Kelson Medeiros"
    assert perfil.categoria == "Docente"
    assert perfil.cargo == "Professor EBTT"
    assert perfil.setor_suap == "DEAD/ZL"
    assert str(perfil) == f"Perfil de {user.username}"

    # Check DadosBrutos
    raw_data = user.suap_raw_data
    assert raw_data is not None
    assert raw_data.data["id"] == 100
    assert "DadosBrutos para" in str(raw_data)

    # Check Vinculo
    assert user.suap_vinculos.count() == 1
    v = user.suap_vinculos.first()
    assert v.identificador == "2080882"
    assert v.tipo == "servidor"
    assert "Vínculo (servidor)" in str(v)


@pytest.mark.django_db
def test_sync_suap_profile_aluno():
    user = User.objects.create_user(username="2021123456", email="aluno@academico.ifrn.edu.br")
    raw_info = {
        "id": 200,
        "identificacao": "2021123456",
        "nome_usual": "Maria Aluna",
        "cpf": "999.888.777-66",
        "tipo_vinculo": "Aluno",
        "tipo_usuario": "Aluno",
        "campus": "CNAT",
        "meus_dados_aluno": {
            "ingresso": "2021.1",
            "email_academico": "maria@academico.ifrn.edu.br",
            "email_escolar": "maria@escolar.ifrn.edu.br",
            "ira": "85.5",
            "curso": "TADS",
            "matriz": "2021-1",
            "qtd_periodos": 6,
            "situacao": "Matriculado",
            "educasenso": "12345678",
        },
    }

    perfil = sync_suap_profile(user, raw_info)

    assert perfil is not None
    assert perfil.matricula == "2021123456"
    assert perfil.tipo_usuario == "Aluno"
    assert perfil.ira == "85.5"
    assert perfil.curso == "TADS"
    assert perfil.situacao == "Matriculado"
    assert perfil.educasenso == "12345678"


@pytest.mark.django_db
def test_sync_suap_profile_usuario_externo():
    user = User.objects.create_user(username="ext_user", email="externo@gmail.com")
    raw_info = {
        "id": 300,
        "identificacao": "ext_user",
        "nome_usual": "Usuario Externo",
        "cpf": "000.111.222-33",
        "tipo_vinculo": "Prestador de Serviço",
        "tipo_usuario": "Usuário Externo",
        "campus": "SUAP",
    }

    perfil = sync_suap_profile(user, raw_info)

    assert perfil is not None
    assert perfil.tipo_usuario == "Usuário Externo"
    assert perfil.cargo == ""
    assert perfil.curso == ""


@pytest.mark.django_db
def test_suap_profile_auth_backend():
    backend = SuapProfileAuthBackend()
    suap_user_info = {
        "identificacao": "2080882",
        "email": "kelson@ifrn.edu.br",
        "nome_registro": "Kelson da Costa Medeiros",
        "tipo_vinculo": "Servidor",
        "categoria": "Docente",
    }

    with patch("django_suap_auth.backends.get_suap_settings") as mock_cfg:
        mock_cfg.return_value = {
            "user_lookup_field": "username",
            "user_attr_map": {
                "username": "identificacao",
                "email": "email",
                ("first_name", "last_name"): "nome_registro",
            },
            "user_info_mappers": ["django_suap_auth.mappers.DefaultAttrMapUserMapper"],
            "json_field": "suap_data",
            "create_user": True,
            "user_defaults": {"is_active": True},
            "first_user_defaults": None,
            "update_fields_on_create": None,
            "update_fields_on_login": None,
        }
        user = backend.authenticate(None, suap_user_info=suap_user_info)

    assert user is not None
    assert user.username == "2080882"
    assert hasattr(user, "suap_profile")
    assert user.suap_profile.categoria == "Docente"


@pytest.mark.django_db
def test_sync_suap_profile_telefones_from_vinculos():
    user = User.objects.create_user(username="tel_test", email="tel@ifrn.edu.br")
    raw_info = {
        "identificacao": "tel_test",
        "meus_vinculos": [
            {
                "identificador": "123",
                "telefones_institucionais": ["(84) 3092-8938"],
            }
        ],
    }
    perfil = sync_suap_profile(user, raw_info)
    assert perfil is not None
    assert "(84) 3092-8938" in perfil.telefones_institucionais


@pytest.mark.django_db
def test_sync_suap_profile_with_vinculo_and_meus_vinculos_matching():
    user = User.objects.create_user(username="2080882", email="kelson.medeiros@ifrn.edu.br")
    course_name = (
        "FIC- Tecendo práticas pedagógicas para a Educação Inclusiva das pessoas com deficiência visual [2025]"
    )
    raw_info = {
        "identificacao": "2080882",
        "nome_social": "",
        "nome_usual": "Kelson Medeiros",
        "nome_registro": "Kelson da Costa Medeiros",
        "nome": "Kelson Medeiros",
        "primeiro_nome": "Kelson",
        "ultimo_nome": "Medeiros",
        "email": "kelson.medeiros@ifrn.edu.br",
        "email_secundario": "kelsoncm@gmail.com",
        "email_google_classroom": "kelson.costa@escolar.ifrn.edu.br",
        "email_academico": "kelson.medeiros@academico.ifrn.edu.br",
        "campus": "ZL",
        "foto": "https://suap.ifrn.edu.br/djtools/arquivo/comum/vinculo/531a48dc-8ae8-4416-84f5-2d8d37aa1207/foto/75x100/",
        "tipo_usuario": "Servidor (Técnico-Administrativo)",
        "email_preferencial": "kelson.medeiros@ifrn.edu.br",
        "cpf": "645.834.571-20",
        "data_de_nascimento": "1978-10-30",
        "sexo": "M",
        "passaporte": "FU507718",
        "id": 159574,
        "matricula": "2080882",
        "rg": "1586368 - SSP/DF - 09/03/1995",
        "filiacao": ["Leonea da Costa Medeiros", "Cicero Jose de Medeiros"],
        "data_nascimento": "1978-10-30",
        "naturalidade": "GAMA/DF",
        "tipo_sanguineo": "A+",
        "url_foto_75x100": "https://suap.ifrn.edu.br/djtools/arquivo/comum/vinculo/531a48dc-8ae8-4416-84f5-2d8d37aa1207/foto/75x100/",
        "url_foto_150x200": "https://suap.ifrn.edu.br/djtools/arquivo/comum/vinculo/531a48dc-8ae8-4416-84f5-2d8d37aa1207/foto/150x200/",
        "tipo_vinculo": "Servidor",
        "vinculo": {
            "matricula": "2080882",
            "nome": "Kelson da Costa Medeiros",
            "setor_suap": "DEAD/ZL",
            "setor_siape": "DEAD/ZL",
            "jornada_trabalho": "40 HORAS SEMANAIS",
            "campus": "ZL",
            "cargo": "ANALISTA DE TEC DA INFORMACAO",
            "funcao": ["SUB-CHEFIA0001 - CME/ZL", "SUB-CHEFIA0001 - CME/ZL"],
            "disciplina_ingresso": "-",
            "categoria": "tecnico_administrativo",
            "telefones_institucionais": ["(84) 3092-8938 (ramal: 8938)"],
            "url_foto_75x100": "https://suap.ifrn.edu.br/djtools/arquivo/comum/vinculo/531a48dc-8ae8-4416-84f5-2d8d37aa1207/foto/75x100/",
            "curriculo_lattes": "http://lattes.cnpq.br/1734494254835148",
        },
        "meus_vinculos": [
            {
                "id": 1588,
                "identificador": "2080882",
                "tipo": "servidor",
                "campus": "ZL",
                "estrangeiro": False,
                "detalhamento": {
                    "cargo": "ANALISTA DE TEC DA INFORMACAO",
                    "categoria": "Técnico Administrativo",
                },
            },
            {
                "id": 159509,
                "identificador": "64583457120",
                "tipo": "prestador_servico",
                "campus": "ZL",
                "estrangeiro": False,
                "detalhamento": None,
            },
            {
                "id": 492751,
                "identificador": "20251ZL00140041",
                "tipo": "aluno",
                "campus": "ZL",
                "estrangeiro": False,
                "detalhamento": {
                    "modalidade": "Qualificação profissional",
                    "nivel_ensino": "Fundamental",
                    "curso": course_name,
                    "ativo": False,
                },
            },
        ],
        "servidores_funcao_ativa": [
            {
                "content_type": "rh.servidor_funcao_ativa",
                "id": 159574,
                "matricula": "208****",
                "nome": "Kelson da Costa Medeiros",
                "funcao": ["SUB-CHEFIA0001 - CME/ZL", "SUB-CHEFIA0001 - CME/ZL"],
                "campus": "CAMPUS AVANÇADO NATAL-ZONA LESTE",
                "setor": "Diretoria da Unidade Educação a Distância (DEAD/ZL)",
                "email_setor": "dead.zl@ifrn.edu.br",
                "telefones_institucionais": ["(84) 3092-8938 (ramal: 8938)"],
                "telefone_campus": "(84) 3092-8907",
                "curriculo_lattes": "http://lattes.cnpq.br/1734494254835148",
            }
        ],
    }

    perfil = sync_suap_profile(user, raw_info)

    assert perfil is not None
    assert perfil.setor_suap == "DEAD/ZL"
    assert perfil.setor_siape == "DEAD/ZL"
    assert perfil.jornada_trabalho == "40 HORAS SEMANAIS"
    assert perfil.cargo == "ANALISTA DE TEC DA INFORMACAO"
    assert perfil.disciplina_ingresso == "-"
    assert perfil.categoria == "Técnico Administrativo"
    assert perfil.curriculo_lattes == "http://lattes.cnpq.br/1734494254835148"
    assert "(84) 3092-8938 (ramal: 8938)" in perfil.telefones_institucionais

    assert user.suap_vinculos.count() == 3
    servidor_vinculo = user.suap_vinculos.get(identificador="2080882")
    assert servidor_vinculo.cargo == "ANALISTA DE TEC DA INFORMACAO"
    assert servidor_vinculo.categoria == "Técnico Administrativo"

    aluno_vinculo = user.suap_vinculos.get(identificador="20251ZL00140041")
    assert aluno_vinculo.curso == course_name
    assert aluno_vinculo.ativo is False


@pytest.mark.django_db
def test_sync_suap_profile_tipo_vinculo_nenhum_copies_tipo_usuario():
    user = User.objects.create_user(username="ext123", email="ext@gmail.com")
    raw_info = {
        "identificacao": "ext123",
        "tipo_vinculo": "Nenhum",
        "tipo_usuario": "Usuário Externo",
    }
    perfil = sync_suap_profile(user, raw_info)
    assert perfil is not None
    assert perfil.tipo_vinculo == "Usuário Externo"


@pytest.mark.django_db
def test_sync_suap_profile_aluno_situacao_precedence():
    user = User.objects.create_user(username="201521510470063", email="kelsoncm@gmail.com")
    raw_info = {
        "identificacao": "201521510470063",
        "matricula": "201521510470063",
        "tipo_usuario": "Aluno",
        "tipo_vinculo": "Nenhum",
        "vinculo": {
            "id": 170685,
            "matricula": "201521510470063",
            "turno": "EAD",
            "curso": "Formação em Educação a Distância EaD",
            "situacao": "Não concluído",
            "situacao_sistemica": "Matriculado no SUAP",
            "matricula_regular": False,
            "cota_sistec": "Não se aplica",
            "cota_mec": "Não se aplica",
        },
        "meus_dados_aluno": {
            "ingresso": "2015/2",
            "ira": "29,75",
            "curso": "151047 - FIC+ Formação em Educação a Distância EaD (CAMPUS AVANÇADO NATAL-ZONA LESTE)",
            "situacao": "Matriculado no SUAP",
        },
    }
    perfil = sync_suap_profile(user, raw_info)
    assert perfil is not None
    assert perfil.situacao == "Não concluído"
    assert perfil.situacao_sistemica == "Matriculado no SUAP"
    assert perfil.tipo_vinculo == "Aluno"
    assert perfil.turno == "EAD"
    assert perfil.matricula_regular is False
    assert perfil.cota_sistec == "Não se aplica"
    assert perfil.cota_mec == "Não se aplica"


@pytest.mark.django_db
def test_profile_model_user_mapper():
    from django_suap_auth.profile.mappers import ProfileModelUserMapper

    mapper = ProfileModelUserMapper()
    user = User.objects.create_user(username="mapper_user", email="m@ifrn.edu.br")
    user_info = {
        "_user": user,
        "identificacao": "mapper_user",
        "nome_usual": "Mapper User",
    }
    attrs = mapper.map_attributes(user_info, {"username": "identificacao"})
    assert attrs["username"] == "mapper_user"
    assert hasattr(user, "suap_profile")

    # Without _user
    user_info_no_user = {"identificacao": "other_user"}
    attrs2 = mapper.map_attributes(user_info_no_user, {"username": "identificacao"})
    assert attrs2["username"] == "other_user"


@pytest.mark.django_db
def test_suap_profile_auth_backend_update_user():
    backend = SuapProfileAuthBackend()
    user = User.objects.create_user(username="update_test", email="old@ifrn.edu.br")

    mapped_attrs = {
        "email": "new@ifrn.edu.br",
        "suap_data": {
            "identificacao": "update_test",
            "nome_usual": "Updated Name",
            "categoria": "Docente",
        },
    }
    cfg = {
        "update_fields_on_login": ["email"],
        "user_defaults": {},
    }
    updated_user = backend.update_user(user, mapped_attrs, cfg)
    assert updated_user.email == "new@ifrn.edu.br"
    assert updated_user.suap_profile.nome_usual == "Updated Name"


def test_profile_backend_helper_functions():
    from datetime import date, datetime

    from django_suap_auth.profile.backends import (
        clean_cpf,
        extract_filiacao,
        extract_telefones_institucionais,
        find_value,
        parse_date,
        sync_suap_profile,
        to_int,
    )

    # parse_date
    assert parse_date(None) is None
    assert parse_date("") is None
    dt = datetime(2020, 1, 1, 12, 0, 0)
    assert parse_date(dt) == date(2020, 1, 1)
    assert parse_date("invalid-date") is None
    assert parse_date(12345) is None

    # clean_cpf
    assert clean_cpf(None) == ""
    assert clean_cpf("") == ""
    assert clean_cpf("123.456.789-01") == "12345678901"

    # extract_telefones_institucionais
    assert extract_telefones_institucionais(None) == []
    assert extract_telefones_institucionais("not-a-dict") == []
    tel_data = {
        "telefones_institucionais": ["(84) 0000-0000"],
        "meus_vinculos": [
            {
                "detalhamento": {
                    "telefones": ["(84) 1111-2222"],
                }
            }
        ],
        "servidores_funcao_ativa": [
            {
                "telefones_institucionais": [
                    {"numero": "(84) 3333-4444", "ramal": "1234"},
                    {"val": "(84) 5555-6666"},
                ]
            }
        ],
    }
    phones = extract_telefones_institucionais(tel_data)
    assert "(84) 0000-0000" in phones
    assert "(84) 1111-2222" in phones
    assert "(84) 3333-4444 (ramal: 1234)" in phones
    assert "(84) 5555-6666" in phones

    # extract_filiacao
    assert extract_filiacao({}) == []
    assert extract_filiacao({"nome_mae": "Mae Silva", "nome_pai": "Pai Silva"}) == ["Mae Silva", "Pai Silva"]
    assert extract_filiacao({"filiacao": "Pai Unico"}) == ["Pai Unico"]
    assert extract_filiacao({"filiacao": 123}) == []

    # find_value
    assert find_value("test_key", None, {"other": 1}, default="def") == "def"

    # to_int
    assert to_int(None) is None
    assert to_int("") is None
    assert to_int("not_a_number") is None
    assert to_int("42") == 42

    # sync_suap_profile invalid input
    assert sync_suap_profile(None, None) is None
    assert sync_suap_profile(None, "invalid") is None


@pytest.mark.django_db
def test_sync_suap_profile_meus_vinculos_fallback_and_detalhamento_ativo():
    user = User.objects.create_user(username="fallback_user", email="fb@ifrn.edu.br")
    raw_info = {
        "identificacao": "different_ident",
        "meus_vinculos": [
            {
                "id": 999,
                "identificador": "vinc_det_active",
                "detalhamento": {
                    "ativo": True,
                    "cargo": "DET CARGO",
                },
            }
        ],
    }
    perfil = sync_suap_profile(user, raw_info)
    assert perfil is not None
    assert perfil.cargo == "DET CARGO"


@pytest.mark.django_db
def test_sync_suap_profile_first_login():
    user = User.objects.create_user(username="first_login_user", email="fl@ifrn.edu.br")
    raw_info = {"identificacao": "first_login_user", "nome_usual": "Primeiro Login"}

    perfil = sync_suap_profile(user, raw_info)
    assert perfil.first_login is not None
    initial_first_login = perfil.first_login

    # Second sync should preserve initial first_login
    raw_info_2 = {"identificacao": "first_login_user", "nome_usual": "Primeiro Login Editado"}
    perfil_updated = sync_suap_profile(user, raw_info_2)
    assert perfil_updated.first_login == initial_first_login


@pytest.mark.django_db
def test_perfil_properties():
    from django_suap_auth.profile.models import Perfil

    user = User.objects.create_user(username="user_props", email="props@ifrn.edu.br")

    # Test show_name fallback chain
    p = Perfil(user=user)
    assert p.show_name == "user_props"

    p.nome_registro = "Registro da Silva"
    assert p.show_name == "Registro da Silva"

    p.nome_social = "Social da Silva"
    assert p.show_name == "Social da Silva"

    p.nome_usual = "Usual da Silva"
    assert p.show_name == "Usual da Silva"

    # Test campus_sigla
    p.campus = "CNAT"
    assert p.campus_sigla == "CNAT"
    p.campus = None
    assert p.campus_sigla == ""

    # Test foto_url
    assert p.foto_url == ""
    p.url_foto_75x100 = "http://example.com/75.jpg"
    assert p.foto_url == "http://example.com/75.jpg"
    p.url_foto_150x200 = "http://example.com/150.jpg"
    assert p.foto_url == "http://example.com/150.jpg"

    # Test settings defaults
    p.settings = None
    assert p.theme_selected == "ifrn25"
    assert p.dyslexia_friendly is False
    assert p.remove_justify is False
    assert p.highlight_links is False
    assert p.stop_animations is False
    assert p.hidden_illustrative_image is False
    assert p.big_cursor is False
    assert p.vlibras_active is True
    assert p.high_line_height is False
    assert p.zoom_level == 100
    assert p.color_mode == "default"
    assert p.menu_position == "bottom"

    # Test custom settings values
    p.settings = {
        "theme": {"selected": "dark"},
        "menu_position": "top",
        "accessibility": {
            "dyslexia_friendly": True,
            "remove_justify": True,
            "highlight_links": True,
            "stop_animations": True,
            "hidden_illustrative_image": True,
            "big_cursor": True,
            "vlibras_active": False,
            "high_line_height": True,
            "zoom_level": "150",
            "color_mode": "high_contrast",
        },
    }
    assert p.theme_selected == "dark"
    assert p.menu_position == "top"
    assert p.dyslexia_friendly is True
    assert p.remove_justify is True
    assert p.highlight_links is True
    assert p.stop_animations is True
    assert p.hidden_illustrative_image is True
    assert p.big_cursor is True
    assert p.vlibras_active is False
    assert p.high_line_height is True
    assert p.zoom_level == 150
    assert p.color_mode == "high_contrast"

    # Test zoom_level invalid value fallback
    p.settings["accessibility"]["zoom_level"] = "invalid"
    assert p.zoom_level == 100


@pytest.mark.django_db
def test_profile_admin_registration():
    import importlib

    from django.contrib import admin

    import django_suap_auth.profile.admin
    from django_suap_auth.profile.admin import CustomUserAdmin
    from django_suap_auth.profile.models import DadosBrutos, Perfil, Vinculo

    user_admin = admin.site._registry.get(User)
    assert isinstance(user_admin, CustomUserAdmin)
    inline_models = [inline.model for inline in user_admin.inlines]
    assert Perfil in inline_models
    assert Vinculo in inline_models
    assert DadosBrutos in inline_models

    # Test foto_preview method on PerfilInline
    perfil_inline_cls = [inline for inline in user_admin.inlines if inline.model == Perfil][0]
    perfil_inline = perfil_inline_cls(User, admin.site)
    p = Perfil(user=User(username="test_foto"), url_foto_150x200="http://example.com/foto.jpg")
    preview = perfil_inline.foto_preview(p)
    assert '<img src="http://example.com/foto.jpg"' in preview

    p_no_foto = Perfil(user=User(username="nofoto"))
    assert perfil_inline.foto_preview(p_no_foto) == "Sem foto"
    assert perfil_inline.foto_preview(None) == "Sem foto"

    # Trigger NotRegistered exception handler in admin.py
    admin.site.unregister(User)
    importlib.reload(django_suap_auth.profile.admin)


@pytest.mark.django_db
def test_migration_0008_populate_user_from_perfil():
    import importlib
    from unittest.mock import MagicMock

    mig = importlib.import_module("django_suap_auth.profile.migrations.0008_dadosbrutos_user_vinculo_user")

    field_perfil = MagicMock()
    field_perfil.name = "perfil"

    mock_dados_brutos = MagicMock()
    mock_dados_brutos._meta.get_fields.return_value = [field_perfil]
    mock_db_obj = MagicMock()
    mock_db_obj.perfil.user_id = 123
    mock_dados_brutos.objects.filter.return_value = [mock_db_obj]

    mock_vinculo = MagicMock()
    mock_vinculo._meta.get_fields.return_value = [field_perfil]
    mock_v_obj = MagicMock()
    mock_v_obj.perfil.user_id = 456
    mock_vinculo.objects.filter.return_value = [mock_v_obj]

    mock_apps = MagicMock()

    def get_model_side_effect(app_label, model_name):
        if model_name == "DadosBrutos":
            return mock_dados_brutos
        return mock_vinculo

    mock_apps.get_model.side_effect = get_model_side_effect

    mig.populate_user_from_perfil(mock_apps, MagicMock())
    assert mock_db_obj.user_id == 123
    assert mock_v_obj.user_id == 456


@pytest.mark.django_db
def test_sync_suap_profile_long_attribute_strings():
    user = User.objects.create_user(username="long_attr_user", email="long@ifrn.edu.br")
    raw_info = {
        "identificacao": "long_attr_user",
        "sexo": "PREFERE NÃO INFORMAR " * 10,
        "tipo_sanguineo": "NÃO INFORMADO " * 10,
        "naturalidade": "CIDADE DE NOME EXTREMAMENTE LONGO " * 5,
        "cpf": "123.456.789-01",
    }
    perfil = sync_suap_profile(user, raw_info)
    assert perfil is not None
    assert len(perfil.sexo) > 10
    assert len(perfil.tipo_sanguineo) > 10
    assert perfil.sexo.startswith("PREFERE NÃO INFORMAR")
    assert perfil.tipo_sanguineo.startswith("NÃO INFORMADO")

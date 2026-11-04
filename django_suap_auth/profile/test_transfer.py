import datetime
import json
from io import StringIO

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.db import models
from django.urls import reverse
from django.utils import timezone

from django_suap_auth.profile import transfer
from django_suap_auth.profile.models import DadosBrutos, Perfil, Vinculo

User = get_user_model()


def _criar_usuario_completo(username="20231234567"):
    user = User.objects.create_user(
        username=username, first_name="Maria", last_name="Aluna", email="maria@academico.ifrn.edu.br", password="x"
    )
    Perfil.objects.create(
        user=user,
        suap_id=200,
        matricula=username,
        nome_usual="Maria Aluna",
        cpf="99988877766",
        data_nascimento=datetime.date(2005, 3, 1),
        filiacao=["Mãe", "Pai"],
        periodo_referencia=2,
        matricula_regular=True,
        settings={"theme": {"selected": "ifrn25"}},
        first_login=timezone.make_aware(datetime.datetime(2026, 1, 2, 3, 4, 5)),
    )
    Vinculo.objects.create(user=user, suap_id=1, identificador=username, tipo="Aluno", campus="CNAT", ativo=True)
    Vinculo.objects.create(user=user, suap_id=2, tipo="Servidor", detalhamento={"cargo": "Bolsista"}, ativo=False)
    DadosBrutos.objects.create(user=user, data={"identificacao": username, "vinculo": {"curso": "TADS"}})
    return user


def _envelope(*usuarios):
    return {"formato": transfer.FORMATO, "versao": transfer.VERSAO, "usuarios": list(usuarios)}


def _sem_data_exportacao(payload):
    return {k: v for k, v in payload.items() if k != "exportado_em"}


# --------------------------------------------------------------------------- exportação / round-trip


@pytest.mark.django_db
def test_exportar_nao_inclui_senha_nem_flags_de_admin():
    user = _criar_usuario_completo()
    user.is_staff = True
    user.is_superuser = True
    user.save()
    dados = json.loads(transfer.para_json(transfer.exportar_usuarios([user])))

    assert dados["formato"] == transfer.FORMATO
    assert dados["versao"] == transfer.VERSAO
    assert "exportado_em" in dados
    exportado = dados["usuarios"][0]
    assert set(exportado["user"]) == {"username", "first_name", "last_name", "email", "is_active"}
    assert exportado["perfil"]["data_nascimento"] == "2005-03-01"
    assert "user" not in exportado["perfil"] and "id" not in exportado["perfil"]
    assert [v["suap_id"] for v in exportado["vinculos"]] == [1, 2]
    assert exportado["dados_brutos"]["vinculo"]["curso"] == "TADS"


@pytest.mark.django_db
def test_exportar_usuario_sem_perfil_nem_dados_brutos():
    user = User.objects.create_user(username="semperfil")
    exportado = transfer.exportar_usuario(user)
    assert exportado["perfil"] is None
    assert exportado["vinculos"] == []
    assert exportado["dados_brutos"] is None


@pytest.mark.django_db
def test_round_trip_exportar_apagar_importar_reproduz_o_usuario():
    user = _criar_usuario_completo()
    texto = transfer.para_json(transfer.exportar_usuarios([user]))
    antes = _sem_data_exportacao(json.loads(texto))

    user.delete()  # simula outro banco
    resultados = transfer.importar_usuarios(transfer.carregar_json(texto))

    assert [(r.username, r.acao) for r in resultados] == [("20231234567", "criar")]
    novo = User.objects.get(username="20231234567")
    depois = _sem_data_exportacao(json.loads(transfer.para_json(transfer.exportar_usuarios([novo]))))
    assert depois == antes
    assert novo.suap_profile.data_nascimento == datetime.date(2005, 3, 1)
    assert novo.suap_profile.first_login == timezone.make_aware(datetime.datetime(2026, 1, 2, 3, 4, 5))
    assert novo.suap_raw_data.data["vinculo"]["curso"] == "TADS"
    assert novo.suap_vinculos.count() == 2
    assert not novo.has_usable_password()
    assert not novo.is_staff and not novo.is_superuser


# --------------------------------------------------------------------------- upsert


@pytest.mark.django_db
def test_upsert_atualiza_sem_mexer_em_senha_flags_e_grupos():
    user = _criar_usuario_completo()
    user.is_staff = True
    user.is_superuser = True
    user.save()
    grupo = Group.objects.create(name="suporte")
    user.groups.add(grupo)
    senha_antes = user.password
    Perfil.objects.filter(user=user).update(nome_social="Mantido")

    payload = _envelope(
        {
            "user": {"username": user.username, "first_name": "Outra", "email": "nova@ifrn.edu.br", "is_active": False},
            "perfil": {"nome_usual": "Novo Nome", "campo_futuro": 1},
            "vinculos": [{"suap_id": 9, "tipo": "Aluno"}],
            "dados_brutos": None,
            "chave_futura": True,
        }
    )
    usuarios = transfer.validar_payload(payload)
    resultados = transfer.importar_usuarios(usuarios)

    assert resultados[0].acao == "atualizar"
    assert any("campo_futuro" in a for a in resultados[0].avisos)
    assert any("chave_futura" in a for a in resultados[0].avisos)
    user.refresh_from_db()
    assert user.password == senha_antes
    assert user.is_staff and user.is_superuser
    assert list(user.groups.all()) == [grupo]
    assert user.first_name == "Outra" and user.last_name == "Aluna"
    assert user.email == "nova@ifrn.edu.br" and user.is_active is False
    assert user.suap_profile.nome_usual == "Novo Nome"
    assert user.suap_profile.nome_social == "Mantido"
    assert list(user.suap_vinculos.values_list("suap_id", flat=True)) == [9]
    assert not DadosBrutos.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_upsert_perfil_nulo_mantem_perfil_e_cria_dados_brutos():
    user = User.objects.create_user(username="u1")
    Perfil.objects.create(user=user, nome_usual="Fica")
    transfer.importar_usuarios(
        transfer.validar_payload(_envelope({"user": {"username": "u1"}, "dados_brutos": [1, 2]}))
    )
    user.refresh_from_db()
    assert user.suap_profile.nome_usual == "Fica"
    assert user.suap_raw_data.data == [1, 2]
    assert user.suap_vinculos.count() == 0


@pytest.mark.django_db
def test_envelope_com_um_unico_usuario():
    payload = {"formato": transfer.FORMATO, "versao": transfer.VERSAO, "user": {"username": "solo"}}
    usuarios = transfer.validar_payload(payload)
    assert [u.username for u in usuarios] == ["solo"]


@pytest.mark.django_db
def test_dry_run_nao_grava_nada():
    user = _criar_usuario_completo()
    payload = _envelope(
        {"user": {"username": user.username, "first_name": "Mudou"}, "vinculos": [], "dados_brutos": None},
        {"user": {"username": "novo"}},
    )
    resultados = transfer.importar_usuarios(transfer.validar_payload(payload), dry_run=True)

    assert [r.acao for r in resultados] == ["atualizar", "criar"]
    user.refresh_from_db()
    assert user.first_name == "Maria"
    assert user.suap_vinculos.count() == 2
    assert DadosBrutos.objects.filter(user=user).exists()
    assert not User.objects.filter(username="novo").exists()


@pytest.mark.django_db
def test_importacao_e_transacional(monkeypatch):
    usuarios = transfer.validar_payload(
        _envelope({"user": {"username": "primeiro"}}, {"user": {"username": "segundo"}})
    )
    original = DadosBrutos.objects.filter
    chamadas = []

    def falha_no_segundo(*args, **kwargs):
        chamadas.append(1)
        if len(chamadas) == 2:
            raise RuntimeError("falha simulada")
        return original(*args, **kwargs)

    monkeypatch.setattr(DadosBrutos.objects, "filter", falha_no_segundo)
    with pytest.raises(RuntimeError):
        transfer.importar_usuarios(usuarios)
    assert not User.objects.filter(username__in=["primeiro", "segundo"]).exists()


# --------------------------------------------------------------------------- validação


@pytest.mark.parametrize(
    "payload, trecho",
    [
        ([], "deve ser um objeto"),
        ({"formato": "outro", "versao": 1, "usuarios": []}, "'formato' deve ser"),
        ({"formato": transfer.FORMATO, "versao": 99, "usuarios": []}, "não suportada"),
        (_envelope(), "ao menos um usuário"),
        ({"formato": transfer.FORMATO, "versao": 1, "usuarios": {}}, "ao menos um usuário"),
        (_envelope("texto"), "usuarios[0]: deve ser um objeto"),
        (_envelope({"perfil": {}}), "usuarios[0].user: obrigatório"),
        (_envelope({"user": "x"}), "usuarios[0].user: deve ser um objeto"),
        (_envelope({"user": {"username": "a", "password": "x"}}), "user.password: campo não permitido"),
        (_envelope({"user": {"username": "a", "is_superuser": True}}), "user.is_superuser: campo não permitido"),
        (_envelope({"user": {"username": "a", "is_active": "sim"}}), "is_active: deve ser true ou false"),
        (_envelope({"user": {"username": "a", "email": 1}}), "user.email: deve ser texto"),
        (_envelope({"user": {"username": " "}}), "user.username: obrigatório"),
        (_envelope({"user": {}}), "user.username: obrigatório"),
        (_envelope({"user": {"username": "a"}}, {"user": {"username": "a"}}), "'a' repetido"),
        (_envelope({"user": {"username": "a"}, "perfil": []}), "perfil: deve ser um objeto"),
        (_envelope({"user": {"username": "a"}, "perfil": {"data_nascimento": "31/02/2000"}}), "data_nascimento"),
        (_envelope({"user": {"username": "a"}, "perfil": {"suap_id": "abc"}}), "perfil.suap_id"),
        (_envelope({"user": {"username": "a"}, "perfil": {"cpf": {"x": 1}}}), "esperado valor simples"),
        (_envelope({"user": {"username": "a"}, "perfil": {"cpf": "1" * 300}}), "excede 256 caracteres"),
        (_envelope({"user": {"username": "a", "first_name": "x" * 500}}), "first_name: excede"),
        (_envelope({"user": {"username": "a"}, "vinculos": {}}), "vinculos: deve ser uma lista"),
        (_envelope({"user": {"username": "a"}, "vinculos": [1]}), "vinculos[0]: deve ser um objeto"),
        (_envelope({"user": {"username": "a"}, "dados_brutos": "x"}), "dados_brutos: deve ser"),
    ],
)
def test_validacao_mensagens_claras(payload, trecho):
    with pytest.raises(transfer.ImportacaoInvalida) as exc:
        transfer.validar_payload(payload)
    assert any(trecho in erro for erro in exc.value.erros), exc.value.erros
    assert trecho.split(":")[0] in str(exc.value)


def test_validacao_aviso_para_campo_desconhecido_do_user():
    usuarios = transfer.validar_payload(_envelope({"user": {"username": "a", "apelido": "b"}}))
    assert any("user.apelido" in a for a in usuarios[0].avisos)


def test_converter_campo_que_nao_aceita_nulo():
    erros: list[str] = []
    assert transfer._converter(models.CharField(max_length=5), None, "x", erros) is None
    assert erros == ["x: não aceita nulo."]


@pytest.mark.parametrize(
    "conteudo, trecho",
    [
        ("{nao e json", "JSON inválido (linha 1"),
        (b"\xff\xfe\x00", "UTF-8"),
    ],
)
def test_carregar_json_invalido(conteudo, trecho):
    with pytest.raises(transfer.ImportacaoInvalida) as exc:
        transfer.carregar_json(conteudo)
    assert trecho in exc.value.erros[0]


def test_carregar_json_aceita_bytes_com_bom():
    texto = json.dumps(_envelope({"user": {"username": "bom"}}))
    assert transfer.carregar_json(b"\xef\xbb\xbf" + texto.encode())[0].username == "bom"


# --------------------------------------------------------------------------- admin


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="root", password="x", email="root@example.com")


@pytest.fixture
def staff(db):
    return User.objects.create_user(username="staff", password="x", is_staff=True)


def _user_admin():
    return admin.site._registry[User]


def _url_importar():
    return reverse(f"admin:{User._meta.app_label}_{User._meta.model_name}_importar")


@pytest.mark.django_db
def test_admin_acao_exportar_json(client, superuser):
    alvo = _criar_usuario_completo()
    client.force_login(superuser)
    url = reverse(f"admin:{User._meta.app_label}_{User._meta.model_name}_changelist")
    response = client.post(url, {"action": "exportar_json", "_selected_action": [alvo.pk]})

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/json")
    assert response["Content-Disposition"].startswith('attachment; filename="usuarios-suap-')
    dados = json.loads(response.content)
    assert [u["user"]["username"] for u in dados["usuarios"]] == [alvo.username]


@pytest.mark.django_db
def test_admin_changelist_mostra_link_importar_so_para_superusuario(client, superuser, staff, settings):
    settings.AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
    url = reverse(f"admin:{User._meta.app_label}_{User._meta.model_name}_changelist")
    client.force_login(superuser)
    assert _url_importar() in client.get(url).content.decode()

    staff.user_permissions.add(Permission.objects.get(codename=f"view_{User._meta.model_name}"))
    client.force_login(staff)
    response = client.get(url)
    assert response.status_code == 200
    assert _url_importar() not in response.content.decode()


@pytest.mark.django_db
def test_admin_exportar_e_importar_negados_para_nao_superusuario(rf, client, staff):
    request = rf.post("/")
    request.user = staff
    assert "exportar_json" not in _user_admin().get_actions(request)
    with pytest.raises(PermissionDenied):
        _user_admin().exportar_json(request, User.objects.all())

    client.force_login(staff)
    assert client.get(_url_importar()).status_code == 403


@pytest.mark.django_db
def test_admin_importar_previa_e_confirmacao(client, superuser):
    _criar_usuario_completo("existente")
    payload = json.dumps(
        _envelope(
            {"user": {"username": "existente"}, "perfil": {"cpf": "1"}, "vinculos": [{"tipo": "Aluno"}]},
            {"user": {"username": "novo", "first_name": "Novo"}, "dados_brutos": {"a": 1}, "extra": 1},
        )
    )
    client.force_login(superuser)

    response = client.get(_url_importar())
    assert response.status_code == 200
    assert "dados pessoais" in response.content.decode()

    arquivo = SimpleUploadedFile("u.json", payload.encode(), content_type="application/json")
    response = client.post(_url_importar(), {"arquivo": arquivo})
    html = response.content.decode()
    assert response.status_code == 200
    assert "Confirmar importação" in html
    assert "existente" in html and "novo" in html and "extra" in html
    assert not User.objects.filter(username="novo").exists()  # prévia não grava

    response = client.post(_url_importar(), {"payload": response.context["payload"], "confirmar": "1"})
    assert response.status_code == 302
    novo = User.objects.get(username="novo")
    assert novo.first_name == "Novo" and novo.suap_raw_data.data == {"a": 1}
    assert User.objects.get(username="existente").suap_vinculos.count() == 1


@pytest.mark.parametrize(
    "dados, trecho",
    [
        ({}, "Selecione um arquivo JSON"),
        ({"confirmar": "1", "payload": ""}, "Nada a importar"),
        ({"arquivo": SimpleUploadedFile("u.json", b"\xff\xfe")}, "UTF-8"),
        ({"arquivo": SimpleUploadedFile("u.json", b"{}")}, "formato"),
    ],
)
@pytest.mark.django_db
def test_admin_importar_erros(client, superuser, dados, trecho):
    client.force_login(superuser)
    response = client.post(_url_importar(), dados)
    assert response.status_code == 200
    assert trecho in response.content.decode()


@pytest.mark.django_db
def test_admin_importar_arquivo_grande(client, superuser, monkeypatch):
    from django_suap_auth.profile import admin as profile_admin

    monkeypatch.setattr(profile_admin, "IMPORTACAO_TAMANHO_MAXIMO", 5)
    client.force_login(superuser)
    response = client.post(_url_importar(), {"arquivo": SimpleUploadedFile("u.json", b"{}      ")})
    assert "limite de 10 MB" in response.content.decode()


# --------------------------------------------------------------------------- comandos


@pytest.mark.django_db
def test_comandos_export_e_import(tmp_path):
    user = _criar_usuario_completo()
    saida = StringIO()
    call_command("export_suap_user", user.username, stdout=saida)
    assert json.loads(saida.getvalue())["usuarios"][0]["user"]["username"] == user.username

    arquivo = tmp_path / "u.json"
    call_command("export_suap_user", user.username, user.username, "-o", str(arquivo), stderr=StringIO())
    assert len(json.loads(arquivo.read_text(encoding="utf-8"))["usuarios"]) == 1

    user.delete()
    saida = StringIO()
    call_command("import_suap_user", str(arquivo), "--dry-run", stdout=saida)
    assert "criar: 20231234567" in saida.getvalue() and "Dry-run" in saida.getvalue()
    assert not User.objects.filter(username="20231234567").exists()

    saida = StringIO()
    call_command("import_suap_user", str(arquivo), stdout=saida)
    assert "1 usuário(s) importado(s)" in saida.getvalue()
    assert User.objects.get(username="20231234567").suap_vinculos.count() == 2


@pytest.mark.django_db
def test_comando_import_mostra_avisos_e_perfil_mantido(tmp_path):
    arquivo = tmp_path / "u.json"
    arquivo.write_text(json.dumps(_envelope({"user": {"username": "a", "x": 1}})), encoding="utf-8")
    saida = StringIO()
    call_command("import_suap_user", str(arquivo), stdout=saida)
    assert "perfil mantido" in saida.getvalue() and "sem dados brutos" in saida.getvalue()
    assert "aviso: usuarios[0].user.x" in saida.getvalue()


@pytest.mark.django_db
def test_comandos_erros(tmp_path):
    with pytest.raises(CommandError, match="não encontrado.*nao-existe"):
        call_command("export_suap_user", "nao-existe")
    with pytest.raises(CommandError, match="Não foi possível ler"):
        call_command("import_suap_user", str(tmp_path / "nada.json"))
    ruim = tmp_path / "ruim.json"
    ruim.write_text("{}", encoding="utf-8")
    with pytest.raises(CommandError, match="Arquivo inválido"):
        call_command("import_suap_user", str(ruim))

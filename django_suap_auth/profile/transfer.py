"""Exportação e importação de usuários com Perfil, Vínculos e Dados brutos.

O formato é um JSON com envelope (``formato``/``versao``) e a lista ``usuarios``. Cada usuário leva
apenas os dados de identificação do ``User`` (nunca senha, ``is_staff``, ``is_superuser``, grupos ou
permissões), o ``Perfil``, os ``Vinculo`` e o ``DadosBrutos.data``.

ATENÇÃO: o conteúdo traz dados pessoais (CPF, RG, e-mails, data de nascimento, filiação etc.).
Não registre o conteúdo em log e guarde/descarte os arquivos com o cuidado exigido pela LGPD.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.utils import timezone

from .models import DadosBrutos, Perfil, Vinculo

FORMATO = "django-suap-auth/usuarios"
VERSAO = 1

USER_FIELDS: tuple[str, ...] = ("username", "first_name", "last_name", "email", "is_active")
# Campos do User que nunca são exportados nem aceitos na importação.
USER_FIELDS_PROIBIDOS: frozenset[str] = frozenset(
    {"password", "is_staff", "is_superuser", "groups", "user_permissions", "last_login", "date_joined", "id", "pk"}
)
CHAVES_USUARIO: frozenset[str] = frozenset({"user", "perfil", "vinculos", "dados_brutos"})


def _campos_editaveis(model: type[models.Model]) -> dict[str, models.Field]:
    """Campos concretos do modelo, exceto a chave primária e o FK ``user``."""
    return {f.name: f for f in model._meta.concrete_fields if not f.primary_key and f.name != "user"}


PERFIL_FIELDS = _campos_editaveis(Perfil)
VINCULO_FIELDS = _campos_editaveis(Vinculo)


class ImportacaoInvalida(ValueError):
    """JSON de importação inválido; ``erros`` lista cada problema encontrado."""

    def __init__(self, erros: list[str]):
        self.erros = erros
        super().__init__("; ".join(erros))


# --------------------------------------------------------------------------- exportação


def _valores(instancia: models.Model, campos: Iterable[str]) -> dict[str, Any]:
    return {nome: getattr(instancia, nome) for nome in campos}


def exportar_usuario(user: Any) -> dict[str, Any]:
    """Serializa um usuário (sem envelope). Valores ainda não convertidos para JSON (datas etc.)."""
    dados_user = {nome: getattr(user, nome) for nome in USER_FIELDS if nome != "username"}
    dados_user = {"username": user.get_username(), **dados_user}

    perfil = Perfil.objects.filter(user=user).first()
    bruto = DadosBrutos.objects.filter(user=user).first()
    vinculos = Vinculo.objects.filter(user=user).order_by("pk")
    return {
        "user": dados_user,
        "perfil": _valores(perfil, PERFIL_FIELDS) if perfil else None,
        "vinculos": [_valores(v, VINCULO_FIELDS) for v in vinculos],
        "dados_brutos": bruto.data if bruto else None,
    }


def exportar_usuarios(users: Iterable[Any]) -> dict[str, Any]:
    """Monta o envelope de exportação para uma lista de usuários."""
    return {
        "formato": FORMATO,
        "versao": VERSAO,
        "exportado_em": timezone.now(),
        "usuarios": [exportar_usuario(u) for u in users],
    }


def para_json(payload: dict[str, Any]) -> str:
    """Converte o envelope em texto JSON (UTF-8, datas em ISO 8601)."""
    return json.dumps(payload, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- validação


@dataclass
class UsuarioImportado:
    """Usuário já validado e com valores convertidos para os tipos dos modelos."""

    username: str
    user: dict[str, Any]
    perfil: dict[str, Any] | None
    vinculos: list[dict[str, Any]]
    dados_brutos: Any
    avisos: list[str] = field(default_factory=list)


def _converter(campo: models.Field, valor: Any, onde: str, erros: list[str]) -> Any:
    if valor is None:
        if not campo.null:
            erros.append(f"{onde}: não aceita nulo.")
        return None
    if isinstance(campo, models.JSONField):
        return valor
    if isinstance(valor, (dict, list)):
        erros.append(f"{onde}: esperado valor simples, recebido {type(valor).__name__}.")
        return None
    try:
        convertido = campo.to_python(valor)
    except ValidationError as exc:
        erros.append(f"{onde}: {' '.join(str(m) for m in exc.messages)}")
        return None
    max_length = getattr(campo, "max_length", None)
    if max_length and isinstance(convertido, str) and len(convertido) > max_length:
        erros.append(f"{onde}: excede {max_length} caracteres.")
    return convertido


def _validar_registro(
    dados: Any, campos: dict[str, models.Field], onde: str, erros: list[str], avisos: list[str]
) -> dict[str, Any] | None:
    if not isinstance(dados, dict):
        erros.append(f"{onde}: deve ser um objeto JSON.")
        return None
    resultado: dict[str, Any] = {}
    for nome, valor in dados.items():
        campo = campos.get(nome)
        if campo is None:
            avisos.append(f"{onde}.{nome}: campo desconhecido, ignorado.")
            continue
        resultado[nome] = _converter(campo, valor, f"{onde}.{nome}", erros)
    return resultado


def _validar_user(dados: Any, onde: str, erros: list[str], avisos: list[str]) -> dict[str, Any] | None:
    if not isinstance(dados, dict):
        erros.append(f"{onde}: deve ser um objeto JSON.")
        return None
    resultado: dict[str, Any] = {}
    for nome, valor in dados.items():
        if nome in USER_FIELDS_PROIBIDOS:
            erros.append(f"{onde}.{nome}: campo não permitido na importação.")
        elif nome not in USER_FIELDS:
            avisos.append(f"{onde}.{nome}: campo desconhecido, ignorado.")
        elif nome == "is_active":
            if not isinstance(valor, bool):
                erros.append(f"{onde}.is_active: deve ser true ou false.")
            resultado[nome] = valor
        elif not isinstance(valor, str):
            erros.append(f"{onde}.{nome}: deve ser texto.")
        else:
            max_length = get_user_model()._meta.get_field(nome).max_length
            if max_length and len(valor) > max_length:
                erros.append(f"{onde}.{nome}: excede {max_length} caracteres.")
            resultado[nome] = valor
    username = resultado.get("username")
    if not isinstance(username, str) or not username.strip():
        erros.append(f"{onde}.username: obrigatório.")
    return resultado


def validar_payload(dados: Any) -> list[UsuarioImportado]:
    """Valida o JSON já decodificado e converte os valores. Levanta ``ImportacaoInvalida``."""
    if not isinstance(dados, dict):
        raise ImportacaoInvalida(["O JSON deve ser um objeto com as chaves 'formato', 'versao' e 'usuarios'."])
    if dados.get("formato") != FORMATO:
        raise ImportacaoInvalida([f"'formato' deve ser '{FORMATO}' (recebido {dados.get('formato')!r})."])
    versao = dados.get("versao")
    if versao != VERSAO:
        raise ImportacaoInvalida([f"'versao' {versao!r} não suportada; esta versão da biblioteca lê a {VERSAO}."])

    # Aceita o envelope com a lista ``usuarios`` ou um único usuário no próprio envelope.
    itens = dados["usuarios"] if "usuarios" in dados else [{k: v for k, v in dados.items() if k in CHAVES_USUARIO}]
    if not isinstance(itens, list) or not itens:
        raise ImportacaoInvalida(["'usuarios' deve ser uma lista com ao menos um usuário."])

    erros: list[str] = []
    resultado: list[UsuarioImportado] = []
    vistos: set[str] = set()
    for i, item in enumerate(itens):
        onde = f"usuarios[{i}]"
        avisos: list[str] = []
        if not isinstance(item, dict):
            erros.append(f"{onde}: deve ser um objeto JSON.")
            continue
        for chave in item.keys() - CHAVES_USUARIO:
            avisos.append(f"{onde}.{chave}: chave desconhecida, ignorada.")
        if "user" not in item:
            erros.append(f"{onde}.user: obrigatório.")
            continue
        user = _validar_user(item["user"], f"{onde}.user", erros, avisos)
        perfil_bruto = item.get("perfil")
        perfil = (
            None
            if perfil_bruto is None
            else _validar_registro(perfil_bruto, PERFIL_FIELDS, f"{onde}.perfil", erros, avisos)
        )
        vinculos_brutos = item.get("vinculos")
        if vinculos_brutos is None:
            vinculos_brutos = []
        vinculos: list[dict[str, Any]] = []
        if not isinstance(vinculos_brutos, list):
            erros.append(f"{onde}.vinculos: deve ser uma lista.")
        else:
            for j, v in enumerate(vinculos_brutos):
                convertido = _validar_registro(v, VINCULO_FIELDS, f"{onde}.vinculos[{j}]", erros, avisos)
                if convertido is not None:
                    vinculos.append(convertido)
        dados_brutos = item.get("dados_brutos")
        if dados_brutos is not None and not isinstance(dados_brutos, (dict, list)):
            erros.append(f"{onde}.dados_brutos: deve ser um objeto JSON, uma lista ou null.")
        if user is None or not isinstance(user.get("username"), str) or not user["username"].strip():
            continue
        username = user["username"]
        if username in vistos:
            erros.append(f"{onde}.user.username: '{username}' repetido no arquivo.")
        vistos.add(username)
        resultado.append(UsuarioImportado(username, user, perfil, vinculos, dados_brutos, avisos))

    if erros:
        raise ImportacaoInvalida(erros)
    return resultado


def carregar_json(texto: str | bytes) -> list[UsuarioImportado]:
    """Decodifica o texto JSON e valida. Levanta ``ImportacaoInvalida`` com mensagem clara."""
    if isinstance(texto, bytes):
        try:
            texto = texto.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ImportacaoInvalida(["O arquivo deve estar em UTF-8."]) from exc
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ImportacaoInvalida([f"JSON inválido (linha {exc.lineno}, coluna {exc.colno}): {exc.msg}."]) from exc
    return validar_payload(dados)


# --------------------------------------------------------------------------- importação


@dataclass
class ResultadoImportacao:
    """Resumo do que foi (ou seria, em dry-run) feito com um usuário."""

    username: str
    acao: str  # "criar" ou "atualizar"
    perfil: bool
    vinculos: int
    dados_brutos: bool
    avisos: list[str]


def importar_usuarios(usuarios: list[UsuarioImportado], dry_run: bool = False) -> list[ResultadoImportacao]:
    """Upsert transacional por username.

    - ``User``: cria (senha inutilizável, sem flags de admin) ou atualiza nome, e-mail e ``is_active``.
      Senha, ``is_staff``, ``is_superuser``, grupos e permissões de usuários existentes não mudam.
    - ``Perfil``: cria ou atualiza os campos informados; ``perfil`` nulo/ausente mantém o atual.
    - ``Vinculo``: substitui todos pelos do arquivo.
    - ``DadosBrutos``: substitui; ``dados_brutos`` nulo/ausente remove o registro atual.

    Em ``dry_run`` tudo roda dentro da transação e é desfeito ao final.
    """
    User = get_user_model()
    username_field = User.USERNAME_FIELD
    resultados: list[ResultadoImportacao] = []
    with transaction.atomic():
        for item in usuarios:
            user = User.objects.filter(**{username_field: item.username}).first()
            criar = user is None
            if criar:
                user = User(**{username_field: item.username})
                user.set_unusable_password()
            for nome, valor in item.user.items():
                if nome != "username":
                    setattr(user, nome, valor)
            user.save()

            if item.perfil is not None:
                Perfil.objects.update_or_create(user=user, defaults=item.perfil)

            Vinculo.objects.filter(user=user).delete()
            Vinculo.objects.bulk_create([Vinculo(user=user, **v) for v in item.vinculos])

            if item.dados_brutos is None:
                DadosBrutos.objects.filter(user=user).delete()
            else:
                DadosBrutos.objects.update_or_create(user=user, defaults={"data": item.dados_brutos})

            resultados.append(
                ResultadoImportacao(
                    username=item.username,
                    acao="criar" if criar else "atualizar",
                    perfil=item.perfil is not None,
                    vinculos=len(item.vinculos),
                    dados_brutos=item.dados_brutos is not None,
                    avisos=item.avisos,
                )
            )
        if dry_run:
            transaction.set_rollback(True)
    return resultados

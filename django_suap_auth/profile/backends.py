import logging
from datetime import datetime

from django_suap_auth.backends import SuapAuthBackend

from .models import DadosBrutos, Perfil, Vinculo

logger = logging.getLogger(__name__)


def parse_date(date_str):
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str.date()
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def clean_cpf(val):
    if not val:
        return ""
    digits = "".join(filter(str.isdigit, str(val)))
    return digits.zfill(11) if digits else ""


def extract_telefones_institucionais(raw_info):
    if not isinstance(raw_info, dict):
        return []

    sources = []

    # 1. Root level keys
    for key in ("telefones_institucionais", "telefones", "telefone_institucional", "telefone_trabalho", "telefone"):
        val = raw_info.get(key)
        if val:
            sources.append(val)

    # 1b. Check vinculo dict
    vinculo = raw_info.get("vinculo")
    if isinstance(vinculo, dict):
        for key in ("telefones_institucionais", "telefones", "telefone_institucional", "telefone_trabalho", "telefone"):
            val = vinculo.get(key)
            if val:
                sources.append(val)

    # 2. Check inside meus_vinculos / vinculos items
    vinculos = raw_info.get("meus_vinculos") or raw_info.get("vinculos") or []
    if isinstance(vinculos, list):
        for v in vinculos:
            if isinstance(v, dict):
                for key in (
                    "telefones_institucionais",
                    "telefones",
                    "telefone_institucional",
                    "telefone_trabalho",
                    "telefone",
                ):
                    val = v.get(key)
                    if val:
                        sources.append(val)
                det = v.get("detalhamento")
                if isinstance(det, dict):
                    for key in (
                        "telefones_institucionais",
                        "telefones",
                        "telefone_institucional",
                        "telefone_trabalho",
                        "telefone",
                    ):
                        val = det.get(key)
                        if val:
                            sources.append(val)

    # 3. Check inside servidores_funcao_ativa items
    sfa = raw_info.get("servidores_funcao_ativa")
    if isinstance(sfa, list):
        for item in sfa:
            if isinstance(item, dict):
                for key in (
                    "telefones_institucionais",
                    "telefones",
                    "telefone_institucional",
                    "telefone_trabalho",
                    "telefone",
                    "telefone_campus",
                ):
                    val = item.get(key)
                    if val:
                        sources.append(val)

    # 4. Collect phone strings and deduplicate
    result = []
    seen = set()

    def _add(phone_str):
        p = str(phone_str).strip()
        if p and p not in seen:
            seen.add(p)
            result.append(p)

    for src in sources:
        if isinstance(src, str):
            _add(src)
        elif isinstance(src, list):
            for item in src:
                if isinstance(item, str):
                    _add(item)
                elif isinstance(item, dict):
                    num = item.get("numero") or item.get("telefone") or item.get("val")
                    if num and str(num).strip():
                        ramal = item.get("ramal")
                        label = f"{num} (ramal: {ramal})" if ramal else str(num)
                        _add(label)

    return result


def extract_filiacao(raw_info):
    raw = raw_info.get("filiacao")
    if not raw:
        mae = raw_info.get("nome_mae") or raw_info.get("mae")
        pai = raw_info.get("nome_pai") or raw_info.get("pai")
        res = []
        if mae and str(mae).strip():
            res.append(str(mae).strip())
        if pai and str(pai).strip():
            res.append(str(pai).strip())
        return res
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def find_value(key_names, *dicts, default=""):
    if isinstance(key_names, str):
        key_names = [key_names]

    for d in dicts:
        if not isinstance(d, dict):
            continue
        for key in key_names:
            if key in d:
                val = d.get(key)
                if val is not None and val != "":
                    return val
    return default


def to_int(val):
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def sync_suap_profile(user, raw_info):
    """Populate and synchronize Perfil, DadosBrutos, and Vinculo models from raw SUAP user info."""
    if not raw_info or not isinstance(raw_info, dict):
        return None

    # Sync DadosBrutos first
    clean_raw_info = {k: v for k, v in raw_info.items() if not k.startswith("_")}
    DadosBrutos.objects.update_or_create(user=user, defaults={"data": clean_raw_info})

    perfil, _ = Perfil.objects.get_or_create(user=user)

    vinculo_dict = raw_info.get("vinculo") if isinstance(raw_info.get("vinculo"), dict) else {}
    meus_vinculos = raw_info.get("meus_vinculos") or raw_info.get("vinculos")
    if not isinstance(meus_vinculos, list):
        meus_vinculos = []

    identificacao = str(raw_info.get("identificacao") or raw_info.get("matricula") or "").strip()

    matched_vinculo = None
    if identificacao and meus_vinculos:
        for item in meus_vinculos:
            if isinstance(item, dict) and str(item.get("identificador", "")).strip() == identificacao:
                matched_vinculo = item
                break
    if not matched_vinculo and meus_vinculos:
        for item in meus_vinculos:
            if isinstance(item, dict) and (
                item.get("ativo")
                or (isinstance(item.get("detalhamento"), dict) and item.get("detalhamento").get("ativo"))
            ):
                matched_vinculo = item
                break
        if not matched_vinculo and isinstance(meus_vinculos[0], dict):
            matched_vinculo = meus_vinculos[0]

    matched_det = (
        matched_vinculo.get("detalhamento")
        if matched_vinculo and isinstance(matched_vinculo.get("detalhamento"), dict)
        else {}
    )
    aluno_info = raw_info.get("meus_dados_aluno") if isinstance(raw_info.get("meus_dados_aluno"), dict) else {}

    # Dict lookup order: raw_info -> matched_det -> matched_vinculo -> vinculo_dict
    sources = [raw_info, matched_det, matched_vinculo or {}, vinculo_dict]
    aluno_sources = sources + [aluno_info]

    # Atributos Comuns
    perfil.suap_id = to_int(find_value(["id", "suap_id"], *sources, default=None))
    perfil.nome_social = find_value("nome_social", *sources)
    perfil.nome_usual = find_value("nome_usual", *sources)
    perfil.nome_registro = find_value(
        ["nome_registro", "nome", "nome_completo"],
        *sources,
        default=f"{user.first_name} {user.last_name}".strip(),
    )
    perfil.campus = find_value("campus", *sources)
    perfil.email_secundario = find_value("email_secundario", *sources)
    perfil.email_google_classroom = find_value("email_google_classroom", *sources)
    perfil.email_academico = find_value("email_academico", *sources)
    perfil.email_preferencial = find_value("email_preferencial", *sources)
    perfil.matricula = find_value(["matricula", "identificacao", "identificador"], *sources)
    perfil.cpf = clean_cpf(find_value("cpf", *sources))
    perfil.rg = find_value("rg", *sources)
    perfil.filiacao = extract_filiacao(raw_info)
    perfil.data_nascimento = parse_date(find_value(["data_nascimento", "data_de_nascimento"], *sources))
    perfil.naturalidade = find_value("naturalidade", *sources)
    perfil.tipo_sanguineo = find_value("tipo_sanguineo", *sources)
    perfil.sexo = find_value("sexo", *sources)
    perfil.passaporte = find_value("passaporte", *sources)
    perfil.url_foto_75x100 = find_value(["url_foto_75x100", "foto"], *sources)
    perfil.url_foto_150x200 = find_value("url_foto_150x200", *sources)
    perfil.tipo_usuario = find_value("tipo_usuario", *sources)
    perfil.tipo_vinculo = find_value(["tipo_vinculo", "tipo"], *sources)
    if not perfil.tipo_vinculo or perfil.tipo_vinculo.strip().lower() == "nenhum":
        perfil.tipo_vinculo = perfil.tipo_usuario
    perfil.telefones_institucionais = extract_telefones_institucionais(raw_info)
    perfil.curriculo_lattes = find_value("curriculo_lattes", *sources)

    # Atributos de Servidor
    perfil.setor_suap = find_value(["setor_suap", "setor"], *sources)
    perfil.setor_siape = find_value("setor_siape", *sources)
    perfil.jornada_trabalho = find_value("jornada_trabalho", *sources)
    perfil.categoria = find_value("categoria", *sources)
    perfil.cargo = find_value("cargo", *sources)
    perfil.disciplina_ingresso = find_value("disciplina_ingresso", *sources)

    # Atributos de Aluno
    perfil.ingresso = find_value("ingresso", *aluno_sources)
    if not perfil.email_academico:
        perfil.email_academico = find_value("email_academico", *aluno_sources)
    perfil.periodo_referencia = to_int(find_value("periodo_referencia", *aluno_sources, default=None))
    perfil.ira = str(find_value("ira", *aluno_sources, default=""))
    perfil.curso = find_value("curso", *aluno_sources)
    perfil.turno = find_value("turno", *aluno_sources)
    perfil.matriz = find_value("matriz", *aluno_sources)
    perfil.qtd_periodos = to_int(find_value("qtd_periodos", *aluno_sources, default=None))
    perfil.situacao = find_value("situacao", *aluno_sources)
    perfil.situacao_sistemica = find_value("situacao_sistemica", *aluno_sources)
    perfil.data_migracao = str(find_value("data_migracao", *aluno_sources, default=""))
    perfil.impressao_digital = bool(find_value("impressao_digital", *aluno_sources, default=False))
    perfil.emitiu_diploma = bool(find_value("emitiu_diploma", *aluno_sources, default=False))
    mat_reg = find_value("matricula_regular", *aluno_sources, default=None)
    perfil.matricula_regular = bool(mat_reg) if mat_reg is not None else None
    perfil.educasenso = str(find_value("educasenso", *aluno_sources, default=""))
    perfil.cota_sistec = find_value("cota_sistec", *aluno_sources)
    perfil.cota_mec = find_value("cota_mec", *aluno_sources)
    perfil.linha_pesquisa = find_value("linha_pesquisa", *aluno_sources)

    if perfil.first_login is None:
        from django.utils.timezone import now

        perfil.first_login = now()

    perfil.save()

    # Sync Vinculos
    if meus_vinculos:
        user.suap_vinculos.all().delete()
        for item in meus_vinculos:
            if isinstance(item, dict):
                det = item.get("detalhamento") if isinstance(item.get("detalhamento"), dict) else {}
                Vinculo.objects.create(
                    user=user,
                    suap_id=to_int(item.get("id")),
                    identificador=str(item.get("identificador", "")),
                    tipo=item.get("tipo", ""),
                    campus=item.get("campus") or det.get("campus"),
                    cargo=item.get("cargo") or det.get("cargo"),
                    categoria=item.get("categoria") or det.get("categoria"),
                    modalidade=item.get("modalidade") or det.get("modalidade"),
                    nivel_ensino=item.get("nivel_ensino") or det.get("nivel_ensino"),
                    curso=item.get("curso") or det.get("curso"),
                    ativo=item.get("ativo") if item.get("ativo") is not None else det.get("ativo"),
                    detalhamento=det,
                    estrangeiro=bool(item.get("estrangeiro", False)),
                )
    elif vinculo_dict:
        user.suap_vinculos.all().delete()
        Vinculo.objects.create(
            user=user,
            suap_id=to_int(vinculo_dict.get("id")),
            identificador=str(vinculo_dict.get("matricula") or identificacao),
            tipo=vinculo_dict.get("tipo_vinculo") or raw_info.get("tipo_vinculo", ""),
            campus=vinculo_dict.get("campus"),
            cargo=vinculo_dict.get("cargo"),
            categoria=vinculo_dict.get("categoria"),
            detalhamento=vinculo_dict,
            ativo=True,
        )

    return perfil


class SuapProfileAuthBackend(SuapAuthBackend):
    """Authentication Backend that automatically populates Perfil, DadosBrutos, and Vinculo models."""

    def create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
        user = super().create_user(lookup_field, lookup_value, mapped_attrs, cfg)
        raw_info = mapped_attrs.get("suap_data", {})
        sync_suap_profile(user, raw_info)
        return user

    def update_user(self, user, mapped_attrs, cfg):
        user = super().update_user(user, mapped_attrs, cfg)
        raw_info = mapped_attrs.get("suap_data", {})
        sync_suap_profile(user, raw_info)
        return user

import logging
from datetime import datetime

from django_suap_auth.backends import SuapAuthBackend

from .models import AlunoProfile, Boletim, Diario, Funcao, HistoricoFuncional, Profile, RawData, Telefone, Vinculo

logger = logging.getLogger(__name__)


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


class SandboxSuapAuthBackend(SuapAuthBackend):
    """Custom backend for sandbox django60.

    Syncs raw SUAP endpoint profile data into 1x1 Profile model, 1x1 RawData model,
    child models (Vinculo, Telefone, Funcao, HistoricoFuncional) and student models
    (AlunoProfile, Diario, Boletim).
    """

    def create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
        user = super().create_user(lookup_field, lookup_value, mapped_attrs, cfg)
        raw_info = mapped_attrs.get("suap_data", {})
        self._sync_profile_data(user, raw_info)
        return user

    def update_user(self, user, mapped_attrs, cfg):
        user = super().update_user(user, mapped_attrs, cfg)
        raw_info = mapped_attrs.get("suap_data", {})
        self._sync_profile_data(user, raw_info)
        return user

    def _sync_profile_data(self, user, raw_info):
        if not raw_info:
            return

        profile, _ = Profile.objects.get_or_create(user=user)

        profile.suap_id = raw_info.get("id")
        profile.matricula = raw_info.get("matricula", raw_info.get("identificacao", ""))
        profile.cpf = raw_info.get("cpf", "")
        profile.rg = raw_info.get("rg", "")
        profile.filiacao = raw_info.get("filiacao", [])
        profile.data_nascimento = parse_date(raw_info.get("data_nascimento") or raw_info.get("data_de_nascimento"))
        profile.naturalidade = raw_info.get("naturalidade", "")
        profile.tipo_sanguineo = raw_info.get("tipo_sanguineo", "")
        profile.sexo = raw_info.get("sexo", "")
        profile.passaporte = raw_info.get("passaporte", "")
        profile.url_foto_75x100 = raw_info.get("url_foto_75x100", "")
        profile.url_foto_150x200 = raw_info.get("url_foto_150x200", "")
        profile.tipo_vinculo = raw_info.get("tipo_vinculo", "")
        profile.tipo_usuario = raw_info.get("tipo_usuario", "")
        profile.campus = raw_info.get("campus", "")
        profile.email_secundario = raw_info.get("email_secundario", "")
        profile.email_google_classroom = raw_info.get("email_google_classroom", "")
        profile.email_academico = raw_info.get("email_academico", "")
        profile.email_preferencial = raw_info.get("email_preferencial", "")
        profile.save()

        # Sync RawData (1x1 with Profile)
        RawData.objects.update_or_create(profile=profile, defaults={"data": raw_info})

        # Sync Vinculos
        meus_vinculos = raw_info.get("meus_vinculos", raw_info.get("vinculos", []))
        if isinstance(meus_vinculos, list):
            profile.vinculos.all().delete()
            for item in meus_vinculos:
                if isinstance(item, dict):
                    Vinculo.objects.create(
                        profile=profile,
                        suap_id=item.get("id"),
                        identificador=str(item.get("identificador", "")),
                        tipo=item.get("tipo", ""),
                        campus=item.get("campus"),
                        estrangeiro=bool(item.get("estrangeiro", False)),
                        detalhamento=item.get("detalhamento"),
                    )

        # Sync Telefones
        telefones_set = set()
        vinculo_dict = raw_info.get("vinculo", {})
        if isinstance(vinculo_dict, dict):
            for tel in vinculo_dict.get("telefones_institucionais", []):
                telefones_set.add((tel, "institucional"))

        servidores_fa = raw_info.get("servidores_funcao_ativa", [])
        if isinstance(servidores_fa, list):
            for sfa in servidores_fa:
                if isinstance(sfa, dict):
                    for tel in sfa.get("telefones_institucionais", []):
                        telefones_set.add((tel, "institucional"))
                    tel_campus = sfa.get("telefone_campus")
                    if tel_campus:
                        telefones_set.add((tel_campus, "campus"))

        if telefones_set:
            profile.telefones.all().delete()
            for tel_num, tel_tipo in telefones_set:
                Telefone.objects.create(profile=profile, numero=tel_num, tipo=tel_tipo)

        # Sync Funcoes
        funcoes_list = []
        if isinstance(vinculo_dict, dict):
            for fn in vinculo_dict.get("funcao", []):
                funcoes_list.append({
                    "nome": fn,
                    "setor": vinculo_dict.get("setor_suap", ""),
                    "campus": vinculo_dict.get("campus", ""),
                })

        if isinstance(servidores_fa, list):
            for sfa in servidores_fa:
                if isinstance(sfa, dict):
                    for fn in sfa.get("funcao", []):
                        funcoes_list.append({
                            "nome": fn,
                            "setor": sfa.get("setor", ""),
                            "email_setor": sfa.get("email_setor", ""),
                            "campus": sfa.get("campus", ""),
                        })

        if funcoes_list:
            profile.funcoes.all().delete()
            seen = set()
            for fdict in funcoes_list:
                key = (fdict["nome"], fdict.get("setor", ""))
                if key not in seen:
                    seen.add(key)
                    Funcao.objects.create(
                        profile=profile,
                        nome=fdict["nome"],
                        setor=fdict.get("setor", ""),
                        email_setor=fdict.get("email_setor", ""),
                        campus=fdict.get("campus", ""),
                    )

        # Sync HistoricoFuncional
        hist_list = raw_info.get("meu_historico_funcional", raw_info.get("historico_funcional", []))
        if isinstance(hist_list, list):
            profile.historicos_funcionais.all().delete()
            for hitem in hist_list:
                if isinstance(hitem, dict):
                    HistoricoFuncional.objects.create(
                        profile=profile,
                        data=str(hitem.get("data", "")),
                        css=hitem.get("css", ""),
                        eventos=hitem.get("eventos", []),
                    )

        # Sync AlunoProfile
        aluno_data = raw_info.get("meus_dados_aluno")
        if isinstance(aluno_data, dict):
            AlunoProfile.objects.update_or_create(
                profile=profile,
                defaults={
                    "ingresso": aluno_data.get("ingresso", ""),
                    "email_academico": aluno_data.get("email_academico", ""),
                    "email_escolar": aluno_data.get("email_escolar", ""),
                    "cpf": aluno_data.get("cpf", ""),
                    "periodo_referencia": aluno_data.get("periodo_referencia"),
                    "ira": str(aluno_data.get("ira", "")),
                    "curso": aluno_data.get("curso", ""),
                    "matriz": aluno_data.get("matriz", ""),
                    "qtd_periodos": aluno_data.get("qtd_periodos"),
                    "situacao": aluno_data.get("situacao", ""),
                    "data_migracao": str(aluno_data.get("data_migracao", "")),
                    "impressao_digital": bool(aluno_data.get("impressao_digital", False)),
                    "emitiu_diploma": bool(aluno_data.get("emitiu_diploma", False)),
                    "educasenso": str(aluno_data.get("educasenso", "")),
                },
            )

        # Sync Diarios
        diarios_list = raw_info.get("diarios", [])
        if isinstance(diarios_list, list) and diarios_list:
            profile.diarios.all().delete()
            for ditem in diarios_list:
                if isinstance(ditem, dict):
                    disc = ditem.get("disciplina", {})
                    disc_desc = disc.get("descricao", "") if isinstance(disc, dict) else str(disc)
                    disc_sigla = disc.get("sigla", "") if isinstance(disc, dict) else ""
                    local = ditem.get("local", {})
                    local_sala = local.get("sala", "") if isinstance(local, dict) else str(local or "")
                    Diario.objects.create(
                        profile=profile,
                        suap_id=ditem.get("id"),
                        disciplina_descricao=disc_desc,
                        disciplina_sigla=disc_sigla,
                        professores=ditem.get("professores", []),
                        horarios=ditem.get("horarios", []),
                        local_sala=local_sala,
                    )

        # Sync Boletins
        boletins_list = raw_info.get("boletins", [])
        if isinstance(boletins_list, list) and boletins_list:
            profile.boletins.all().delete()
            for bitem in boletins_list:
                if isinstance(bitem, dict):
                    Boletim.objects.create(
                        profile=profile,
                        codigo_diario=str(bitem.get("codigo_diario", "")),
                        disciplina=bitem.get("disciplina", ""),
                        carga_horaria=bitem.get("carga_horaria"),
                        carga_horaria_cumprida=bitem.get("carga_horaria_cumprida"),
                        numero_faltas=bitem.get("numero_faltas"),
                        percentual_carga_horaria_frequentada=bitem.get("percentual_carga_horaria_frequentada"),
                        situacao=bitem.get("situacao", ""),
                        media_disciplina=str(bitem.get("media_disciplina", "") or ""),
                        media_final_disciplina=str(bitem.get("media_final_disciplina", "") or ""),
                    )

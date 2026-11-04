from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from . import transfer
from .models import DadosBrutos, Perfil, Vinculo
from .widgets import InlineJSONEditorWidget

User = get_user_model()


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = "Perfil SUAP"
    fk_name = "user"
    extra = 0
    max_num = 1
    readonly_fields = ("foto_preview",)
    fieldsets = (
        (
            "Identificação e Dados Gerais",
            {
                "fields": (
                    ("suap_id", "matricula"),
                    ("nome_usual", "nome_social", "nome_registro"),
                    ("campus", "cpf", "rg"),
                    ("filiacao", "data_nascimento", "naturalidade"),
                    ("tipo_sanguineo", "sexo", "passaporte"),
                    ("foto_preview", "url_foto_75x100", "url_foto_150x200"),
                    ("tipo_usuario", "tipo_vinculo"),
                    "curriculo_lattes",
                )
            },
        ),
        (
            "E-mails e Contatos",
            {
                "fields": (
                    ("email_secundario", "email_google_classroom"),
                    ("email_academico", "email_preferencial"),
                    "telefones_institucionais",
                )
            },
        ),
        (
            "Atributos de Servidor",
            {
                "classes": ("collapse",),
                "fields": (
                    ("setor_suap", "setor_siape"),
                    ("jornada_trabalho", "categoria"),
                    ("cargo", "disciplina_ingresso"),
                ),
            },
        ),
        (
            "Atributos de Aluno",
            {
                "classes": ("collapse",),
                "fields": (
                    ("ingresso", "periodo_referencia", "ira"),
                    ("curso", "turno", "matriz"),
                    ("qtd_periodos", "situacao", "situacao_sistemica"),
                    ("data_migracao", "educasenso"),
                    ("impressao_digital", "emitiu_diploma", "matricula_regular"),
                    ("cota_sistec", "cota_mec", "linha_pesquisa"),
                ),
            },
        ),
        (
            "Preferências e Acesso",
            {
                "classes": ("collapse",),
                "fields": (
                    "settings",
                    "first_login",
                ),
            },
        ),
    )

    @admin.display(description="Foto de Perfil")
    def foto_preview(self, obj):
        if obj and obj.foto_url:
            return mark_safe(
                f'<img src="{obj.foto_url}" '
                'style="max-height: 150px; max-width: 150px; border-radius: 8px; '
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
            )
        return "Sem foto"

    class Media:
        css = {
            "all": ("django_suap_auth/css/profile_admin.css",),
        }


class DadosBrutosInline(admin.StackedInline):
    model = DadosBrutos
    extra = 0
    max_num = 1
    verbose_name_plural = "Dados Brutos SUAP"
    classes = ("collapse",)
    formfield_overrides = {
        models.JSONField: {"widget": InlineJSONEditorWidget},
    }


class VinculoInline(admin.TabularInline):
    model = Vinculo
    extra = 0
    verbose_name_plural = "Vínculos SUAP"


# Tamanho máximo do arquivo aceito na página "Importar usuários".
IMPORTACAO_TAMANHO_MAXIMO = 10 * 1024 * 1024


class ImportarUsuariosForm(forms.Form):
    arquivo = forms.FileField(label=_("Arquivo JSON"), required=False)
    payload = forms.CharField(widget=forms.HiddenInput, required=False)


class CustomUserAdmin(UserAdmin):
    inlines = [PerfilInline, VinculoInline, DadosBrutosInline]
    actions = ["exportar_json"]
    change_list_template = "admin/django_suap_auth_profile/user/change_list.html"
    importar_template = "admin/django_suap_auth_profile/user/importar.html"
    filter_horizontal = ("groups",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # ------------------------------------------------------------------ exportar / importar (só superusuário)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop("exportar_json", None)
        return actions

    @admin.action(description=_("Exportar (JSON) com perfil, vínculos e dados brutos"))
    def exportar_json(self, request, queryset):
        if not request.user.is_superuser:
            raise PermissionDenied
        payload = transfer.exportar_usuarios(queryset.order_by(queryset.model.USERNAME_FIELD))
        nome = f"usuarios-suap-{timezone.now():%Y%m%d-%H%M%S}.json"
        response = HttpResponse(transfer.para_json(payload), content_type="application/json; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{nome}"'
        return response

    def get_urls(self):
        custom_urls = [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_importar",
            ),
        ]
        return custom_urls + super().get_urls()

    def importar_view(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied
        form = ImportarUsuariosForm(request.POST, request.FILES) if request.method == "POST" else ImportarUsuariosForm()
        erros: list[str] = []
        previa = None
        payload = ""
        if form.is_bound and form.is_valid():
            if "confirmar" in request.POST:
                payload = form.cleaned_data["payload"]
                if not payload:
                    erros.append(str(_("Nada a importar: envie o arquivo novamente.")))
            elif form.cleaned_data["arquivo"]:
                arquivo = form.cleaned_data["arquivo"]
                if arquivo.size > IMPORTACAO_TAMANHO_MAXIMO:
                    erros.append(str(_("Arquivo maior que o limite de 10 MB.")))
                else:
                    try:
                        payload = arquivo.read().decode("utf-8-sig")
                    except UnicodeDecodeError:
                        erros.append(str(_("O arquivo deve estar em UTF-8.")))
            else:
                erros.append(str(_("Selecione um arquivo JSON.")))
            if payload:
                try:
                    usuarios = transfer.carregar_json(payload)
                    if "confirmar" in request.POST:
                        resultados = transfer.importar_usuarios(usuarios)
                        criados = sum(1 for r in resultados if r.acao == "criar")
                        self.message_user(
                            request,
                            _("Importação concluída: %(criados)d criado(s), %(atualizados)d atualizado(s).")
                            % {"criados": criados, "atualizados": len(resultados) - criados},
                            messages.SUCCESS,
                        )
                        return HttpResponseRedirect(
                            reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist")
                        )
                    previa = transfer.importar_usuarios(usuarios, dry_run=True)
                except transfer.ImportacaoInvalida as exc:
                    erros.extend(exc.erros)
                    payload = ""
        context = {
            **self.admin_site.each_context(request),
            "title": _("Importar usuários"),
            "opts": self.opts,
            "form": form,
            "erros": erros,
            "previa": previa,
            "payload": payload,
        }
        return TemplateResponse(request, self.importar_template, context)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)

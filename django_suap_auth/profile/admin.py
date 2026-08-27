from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from django_json_widget.widgets import JSONEditorWidget

from .models import DadosBrutos, Perfil, Vinculo

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
        models.JSONField: {"widget": JSONEditorWidget},
    }


class VinculoInline(admin.TabularInline):
    model = Vinculo
    extra = 0
    verbose_name_plural = "Vínculos SUAP"


class CustomUserAdmin(UserAdmin):
    inlines = [PerfilInline, VinculoInline, DadosBrutosInline]
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


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)

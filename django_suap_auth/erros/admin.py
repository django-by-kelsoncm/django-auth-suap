from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import SincronizacaoErro


@admin.register(SincronizacaoErro)
class SincronizacaoErroAdmin(SimpleHistoryAdmin):
    list_display = ("id", "usuario", "endpoint", "status_code", "data_ocorrencia")
    list_filter = ("status_code", "data_ocorrencia")
    search_fields = ("endpoint", "mensagem_erro", "usuario__username", "usuario__email")
    readonly_fields = ("data_ocorrencia",)
    date_hierarchy = "data_ocorrencia"

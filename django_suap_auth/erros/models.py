from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class SincronizacaoErro(models.Model):
    """Registro de erros ocorridos durante a sincronização de endpoints secundários."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="erros_sincronizacao",
        verbose_name=_("usuário"),
        null=True,
        blank=True,
    )
    endpoint = models.CharField(_("endpoint"), max_length=256)
    status_code = models.IntegerField(_("status HTTP"), null=True, blank=True)
    mensagem_erro = models.TextField(_("mensagem de erro"))
    data_ocorrencia = models.DateTimeField(_("data da ocorrência"), auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("erro de sincronização")
        verbose_name_plural = _("erros de sincronização")
        ordering = ["-data_ocorrencia"]

    def __str__(self):
        status_info = f" [{self.status_code}]" if self.status_code is not None else ""
        return f"Erro em {self.endpoint}{status_info}: {self.mensagem_erro[:50]}"

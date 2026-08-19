from django.conf import settings
from django.db import models


class Perfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suap_profile")

    # Atributos Comuns (Todos os Usuários)
    suap_id = models.IntegerField(null=True, blank=True)
    matricula = models.CharField(max_length=50, null=True, blank=True)
    nome_usual = models.CharField(max_length=256, null=True, blank=True)
    nome_social = models.CharField(max_length=256, null=True, blank=True)
    nome_registro = models.CharField(max_length=256, null=True, blank=True)
    campus = models.CharField(max_length=100, null=True, blank=True)
    email_secundario = models.EmailField(null=True, blank=True)
    email_google_classroom = models.EmailField(null=True, blank=True)
    email_academico = models.EmailField(null=True, blank=True)
    email_preferencial = models.EmailField(null=True, blank=True)
    cpf = models.CharField(max_length=20, null=True, blank=True)
    rg = models.CharField(max_length=100, null=True, blank=True)
    filiacao = models.JSONField(default=list, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    naturalidade = models.CharField(max_length=100, null=True, blank=True)
    tipo_sanguineo = models.CharField(max_length=10, null=True, blank=True)
    sexo = models.CharField(max_length=10, null=True, blank=True)
    passaporte = models.CharField(max_length=50, null=True, blank=True)
    url_foto_75x100 = models.URLField(max_length=500, null=True, blank=True)
    url_foto_150x200 = models.URLField(max_length=500, null=True, blank=True)
    tipo_usuario = models.CharField(max_length=100, null=True, blank=True)
    tipo_vinculo = models.CharField(max_length=100, null=True, blank=True)
    telefones_institucionais = models.JSONField(default=list, null=True, blank=True)
    curriculo_lattes = models.CharField(max_length=100, null=True, blank=True)

    # Atributos de Servidor
    setor_suap = models.CharField(max_length=100, null=True, blank=True)
    setor_siape = models.CharField(max_length=100, null=True, blank=True)
    jornada_trabalho = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    disciplina_ingresso = models.CharField(max_length=100, null=True, blank=True)

    # Atributos de Aluno
    ingresso = models.CharField(max_length=50, null=True, blank=True)
    periodo_referencia = models.IntegerField(null=True, blank=True)
    ira = models.CharField(max_length=20, null=True, blank=True)
    curso = models.CharField(max_length=255, null=True, blank=True)
    turno = models.CharField(max_length=255, null=True, blank=True)
    matriz = models.CharField(max_length=255, null=True, blank=True)
    qtd_periodos = models.IntegerField(null=True, blank=True)
    situacao = models.CharField(max_length=100, null=True, blank=True)
    situacao_sistemica = models.CharField(max_length=100, null=True, blank=True)
    data_migracao = models.CharField(max_length=50, null=True, blank=True)
    impressao_digital = models.BooleanField(default=False, null=True, blank=True)
    emitiu_diploma = models.BooleanField(default=False, null=True, blank=True)
    matricula_regular = models.BooleanField(default=None, null=True, blank=True)
    educasenso = models.CharField(max_length=100, null=True, blank=True)
    cota_sistec = models.CharField(max_length=100, null=True, blank=True)
    cota_mec = models.CharField(max_length=100, null=True, blank=True)
    linha_pesquisa = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"Perfil de {self.user.username}"


class DadosBrutos(models.Model):
    perfil = models.OneToOneField(Perfil, on_delete=models.CASCADE, related_name="raw_data")
    data = models.JSONField(default=dict, null=True, blank=True)

    class Meta:
        verbose_name = "Dado Bruto"
        verbose_name_plural = "Dados Brutos"

    def __str__(self):
        return f"DadosBrutos para {self.perfil.user.username}"


class Vinculo(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="vinculos")
    suap_id = models.IntegerField(null=True, blank=True)
    identificador = models.CharField(max_length=50, null=True, blank=True)
    tipo = models.CharField(max_length=50, null=True, blank=True)
    campus = models.CharField(max_length=256, null=True, blank=True)
    cargo = models.CharField(max_length=256, null=True, blank=True)
    categoria = models.CharField(max_length=256, null=True, blank=True)
    modalidade = models.CharField(max_length=256, null=True, blank=True)
    nivel_ensino = models.CharField(max_length=256, null=True, blank=True)
    curso = models.CharField(max_length=256, null=True, blank=True)
    ativo = models.BooleanField(default=None, null=True, blank=True)
    detalhamento = models.JSONField(default=dict, null=True, blank=True)
    estrangeiro = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = "Vínculo"
        verbose_name_plural = "Vínculos"

    def __str__(self):
        return f"Vínculo ({self.tipo}) - {self.identificador}"

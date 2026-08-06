from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    suap_id = models.IntegerField(null=True, blank=True)
    matricula = models.CharField(max_length=50, blank=True)
    cpf = models.CharField(max_length=20, blank=True)
    rg = models.CharField(max_length=100, blank=True)
    filiacao = models.JSONField(default=list, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    naturalidade = models.CharField(max_length=100, blank=True)
    tipo_sanguineo = models.CharField(max_length=10, blank=True)
    sexo = models.CharField(max_length=10, blank=True)
    passaporte = models.CharField(max_length=50, blank=True)
    url_foto_75x100 = models.URLField(max_length=500, blank=True)
    url_foto_150x200 = models.URLField(max_length=500, blank=True)
    tipo_vinculo = models.CharField(max_length=100, blank=True)
    tipo_usuario = models.CharField(max_length=100, blank=True)
    campus = models.CharField(max_length=100, blank=True)
    email_secundario = models.EmailField(blank=True)
    email_google_classroom = models.EmailField(blank=True)
    email_academico = models.EmailField(blank=True)
    email_preferencial = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class RawData(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="raw_data")
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RawData for {self.profile.user.username}"


class AlunoProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="aluno_profile")
    ingresso = models.CharField(max_length=50, blank=True)
    email_academico = models.EmailField(blank=True)
    email_escolar = models.EmailField(blank=True)
    cpf = models.CharField(max_length=20, blank=True)
    periodo_referencia = models.IntegerField(null=True, blank=True)
    ira = models.CharField(max_length=20, blank=True)
    curso = models.CharField(max_length=255, blank=True)
    matriz = models.CharField(max_length=255, blank=True)
    qtd_periodos = models.IntegerField(null=True, blank=True)
    situacao = models.CharField(max_length=100, blank=True)
    data_migracao = models.CharField(max_length=50, blank=True)
    impressao_digital = models.BooleanField(default=False)
    emitiu_diploma = models.BooleanField(default=False)
    educasenso = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"AlunoProfile for {self.profile.user.username}"


class Vinculo(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="vinculos")
    suap_id = models.IntegerField(null=True, blank=True)
    identificador = models.CharField(max_length=50, blank=True)
    tipo = models.CharField(max_length=50, blank=True)
    campus = models.CharField(max_length=100, null=True, blank=True)
    estrangeiro = models.BooleanField(default=False)
    detalhamento = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return f"Vinculo ({self.tipo}) - {self.identificador}"


class Telefone(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="telefones")
    numero = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, default="institucional")

    def __str__(self):
        return f"Telefone ({self.tipo}): {self.numero}"


class Funcao(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="funcoes")
    nome = models.CharField(max_length=255)
    setor = models.CharField(max_length=255, blank=True)
    email_setor = models.EmailField(blank=True)
    campus = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Função: {self.nome}"


class HistoricoFuncional(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="historicos_funcionais")
    data = models.CharField(max_length=50)
    css = models.CharField(max_length=50, blank=True)
    eventos = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Histórico Funcional - {self.data}"


class Diario(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="diarios")
    suap_id = models.IntegerField(null=True, blank=True)
    disciplina_descricao = models.CharField(max_length=255, blank=True)
    disciplina_sigla = models.CharField(max_length=50, blank=True)
    professores = models.JSONField(default=list, blank=True)
    horarios = models.JSONField(default=list, blank=True)
    local_sala = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Diário: {self.disciplina_sigla} - {self.disciplina_descricao}"


class Boletim(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="boletins")
    codigo_diario = models.CharField(max_length=50, blank=True)
    disciplina = models.CharField(max_length=255, blank=True)
    carga_horaria = models.IntegerField(null=True, blank=True)
    carga_horaria_cumprida = models.IntegerField(null=True, blank=True)
    numero_faltas = models.IntegerField(null=True, blank=True)
    percentual_carga_horaria_frequentada = models.FloatField(null=True, blank=True)
    situacao = models.CharField(max_length=50, blank=True)
    media_disciplina = models.CharField(max_length=20, blank=True)
    media_final_disciplina = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Boletim: {self.disciplina} ({self.situacao})"

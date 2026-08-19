import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Perfil",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("suap_id", models.IntegerField(blank=True, null=True)),
                ("nome_social", models.CharField(blank=True, max_length=256)),
                ("nome_usual", models.CharField(blank=True, max_length=256)),
                ("campus", models.CharField(blank=True, max_length=100)),
                ("email_secundario", models.EmailField(blank=True, max_length=254)),
                ("email_google_classroom", models.EmailField(blank=True, max_length=254)),
                ("email_academico", models.EmailField(blank=True, max_length=254)),
                ("email_preferencial", models.EmailField(blank=True, max_length=254)),
                ("matricula", models.CharField(blank=True, max_length=50)),
                ("cpf", models.CharField(blank=True, max_length=20)),
                ("rg", models.CharField(blank=True, max_length=100)),
                ("filiacao", models.JSONField(blank=True, default=list)),
                ("data_nascimento", models.DateField(blank=True, null=True)),
                ("naturalidade", models.CharField(blank=True, max_length=100)),
                ("tipo_sanguineo", models.CharField(blank=True, max_length=10)),
                ("sexo", models.CharField(blank=True, max_length=10)),
                ("passaporte", models.CharField(blank=True, max_length=50)),
                ("url_foto_75x100", models.URLField(blank=True, max_length=500)),
                ("url_foto_150x200", models.URLField(blank=True, max_length=500)),
                ("tipo_usuario", models.CharField(blank=True, max_length=100)),
                ("tipo_vinculo", models.CharField(blank=True, max_length=100)),
                ("telefones_institucionais", models.JSONField(blank=True, default=list)),
                ("curriculo_lattes", models.CharField(blank=True, max_length=100)),
                ("setor_suap", models.CharField(blank=True, max_length=100)),
                ("setor_siape", models.CharField(blank=True, max_length=100)),
                ("jornada_trabalho", models.CharField(blank=True, max_length=100)),
                ("categoria", models.CharField(blank=True, max_length=100)),
                ("cargo", models.CharField(blank=True, max_length=100)),
                ("disciplina_ingresso", models.CharField(blank=True, max_length=100)),
                ("ingresso", models.CharField(blank=True, max_length=50)),
                ("email_escolar", models.EmailField(blank=True, max_length=254)),
                ("periodo_referencia", models.IntegerField(blank=True, null=True)),
                ("ira", models.CharField(blank=True, max_length=20)),
                ("curso", models.CharField(blank=True, max_length=255)),
                ("matriz", models.CharField(blank=True, max_length=255)),
                ("qtd_periodos", models.IntegerField(blank=True, null=True)),
                ("situacao", models.CharField(blank=True, max_length=100)),
                ("data_migracao", models.CharField(blank=True, max_length=50)),
                ("impressao_digital", models.BooleanField(default=False)),
                ("emitiu_diploma", models.BooleanField(default=False)),
                ("educasenso", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suap_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil",
                "verbose_name_plural": "Perfis",
            },
        ),
        migrations.CreateModel(
            name="DadosBrutos",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "perfil",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="raw_data",
                        to="django_suap_auth_profile.perfil",
                    ),
                ),
            ],
            options={
                "verbose_name": "Dado Bruto",
                "verbose_name_plural": "Dados Brutos",
            },
        ),
        migrations.CreateModel(
            name="Vinculo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("suap_id", models.IntegerField(blank=True, null=True)),
                ("identificador", models.CharField(blank=True, max_length=50)),
                ("tipo", models.CharField(blank=True, max_length=50)),
                ("campus", models.CharField(blank=True, max_length=256, null=True)),
                ("cargo", models.CharField(blank=True, max_length=256, null=True)),
                ("categoria", models.CharField(blank=True, max_length=256, null=True)),
                ("modalidade", models.CharField(blank=True, max_length=256, null=True)),
                ("nivel_ensino", models.CharField(blank=True, max_length=256, null=True)),
                ("curso", models.CharField(blank=True, max_length=256, null=True)),
                ("ativo", models.BooleanField(blank=True, default=None, null=True)),
                ("detalhamento", models.JSONField(blank=True, default=dict, null=True)),
                ("estrangeiro", models.BooleanField(default=False)),
                (
                    "perfil",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vinculos",
                        to="django_suap_auth_profile.perfil",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vínculo",
                "verbose_name_plural": "Vínculos",
            },
        ),
    ]

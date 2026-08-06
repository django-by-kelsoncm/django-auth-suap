import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlunoProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ingresso", models.CharField(blank=True, max_length=50)),
                ("email_academico", models.EmailField(blank=True, max_length=254)),
                ("email_escolar", models.EmailField(blank=True, max_length=254)),
                ("cpf", models.CharField(blank=True, max_length=20)),
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
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aluno_profile",
                        to="home.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Diario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("suap_id", models.IntegerField(blank=True, null=True)),
                ("disciplina_descricao", models.CharField(blank=True, max_length=255)),
                ("disciplina_sigla", models.CharField(blank=True, max_length=50)),
                ("professores", models.JSONField(blank=True, default=list)),
                ("horarios", models.JSONField(blank=True, default=list)),
                ("local_sala", models.CharField(blank=True, max_length=255)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="diarios",
                        to="home.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Boletim",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo_diario", models.CharField(blank=True, max_length=50)),
                ("disciplina", models.CharField(blank=True, max_length=255)),
                ("carga_horaria", models.IntegerField(blank=True, null=True)),
                ("carga_horaria_cumprida", models.IntegerField(blank=True, null=True)),
                ("numero_faltas", models.IntegerField(blank=True, null=True)),
                ("percentual_carga_horaria_frequentada", models.FloatField(blank=True, null=True)),
                ("situacao", models.CharField(blank=True, max_length=50)),
                ("media_disciplina", models.CharField(blank=True, max_length=20)),
                ("media_final_disciplina", models.CharField(blank=True, max_length=20)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="boletins",
                        to="home.profile",
                    ),
                ),
            ],
        ),
    ]

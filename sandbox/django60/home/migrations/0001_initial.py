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
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("suap_id", models.IntegerField(blank=True, null=True)),
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
                ("tipo_vinculo", models.CharField(blank=True, max_length=100)),
                ("tipo_usuario", models.CharField(blank=True, max_length=100)),
                ("campus", models.CharField(blank=True, max_length=100)),
                ("email_secundario", models.EmailField(blank=True, max_length=254)),
                ("email_google_classroom", models.EmailField(blank=True, max_length=254)),
                ("email_academico", models.EmailField(blank=True, max_length=254)),
                ("email_preferencial", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RawData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="raw_data",
                        to="home.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Vinculo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("suap_id", models.IntegerField(blank=True, null=True)),
                ("identificador", models.CharField(blank=True, max_length=50)),
                ("tipo", models.CharField(blank=True, max_length=50)),
                ("campus", models.CharField(blank=True, max_length=100, null=True)),
                ("estrangeiro", models.BooleanField(default=False)),
                ("detalhamento", models.JSONField(blank=True, default=dict, null=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vinculos",
                        to="home.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Telefone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero", models.CharField(max_length=100)),
                ("tipo", models.CharField(default="institucional", max_length=50)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telefones",
                        to="home.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Funcao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=255)),
                ("setor", models.CharField(blank=True, max_length=255)),
                ("email_setor", models.EmailField(blank=True, max_length=254)),
                ("campus", models.CharField(blank=True, max_length=255)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="funcoes",
                        to="home.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HistoricoFuncional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.CharField(max_length=50)),
                ("css", models.CharField(blank=True, max_length=50)),
                ("eventos", models.JSONField(blank=True, default=list)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historicos_funcionais",
                        to="home.profile",
                    ),
                ),
            ],
        ),
    ]

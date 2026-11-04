from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from django_suap_auth.profile import transfer


class Command(BaseCommand):
    help = (
        "Importa usuários (perfil, vínculos e dados brutos) de um JSON gerado por export_suap_user, "
        "com upsert por username. Não altera senha, is_staff, is_superuser, grupos nem permissões."
    )

    def add_arguments(self, parser):
        parser.add_argument("arquivo", help="Arquivo JSON a importar.")
        parser.add_argument(
            "--dry-run", action="store_true", help="Valida e mostra o que seria feito, sem gravar nada."
        )

    def handle(self, *args, arquivo: str, dry_run: bool = False, **options):
        try:
            conteudo = Path(arquivo).read_bytes()
        except OSError as exc:
            raise CommandError(f"Não foi possível ler '{arquivo}': {exc.strerror}") from exc
        try:
            usuarios = transfer.carregar_json(conteudo)
        except transfer.ImportacaoInvalida as exc:
            raise CommandError("Arquivo inválido:\n  - " + "\n  - ".join(exc.erros)) from exc

        resultados = transfer.importar_usuarios(usuarios, dry_run=dry_run)
        for r in resultados:
            perfil = "perfil" if r.perfil else "perfil mantido"
            brutos = "dados brutos" if r.dados_brutos else "sem dados brutos"
            self.stdout.write(f"{r.acao}: {r.username} ({perfil}, {r.vinculos} vínculo(s), {brutos})")
            for aviso in r.avisos:
                self.stdout.write(self.style.WARNING(f"  aviso: {aviso}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: nada foi gravado."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{len(resultados)} usuário(s) importado(s)."))

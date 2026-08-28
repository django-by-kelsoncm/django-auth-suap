from django.core.management.base import BaseCommand

from django_suap_auth.audit.services import archive_audit_events


class Command(BaseCommand):
    help = "Arquiva eventos de auditoria antigos em arquivo comprimido JSONL (.gz) para retenção LGPD de 5 anos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="Dias de retenção no banco relacional quente (padrão: 365 dias)",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Caminho do arquivo de destino .jsonl.gz (opcional)",
        )
        parser.add_argument(
            "--no-delete",
            action="store_true",
            help="Se especificado, apenas exporta o arquivo sem deletar os registros do banco relacional",
        )

    def handle(self, *args, **options):
        days = options["days"]
        output = options["output"]
        delete_archived = not options["no_delete"]

        self.stdout.write(f"Iniciando arquivamento de eventos anteriores a {days} dias...")
        count = archive_audit_events(days_older=days, output_path=output, delete_archived=delete_archived)
        self.stdout.write(
            self.style.SUCCESS(f"Arquivamento concluído com sucesso. Total de registros processados: {count}")
        )

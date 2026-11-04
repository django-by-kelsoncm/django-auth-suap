from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from django_suap_auth.profile import transfer


class Command(BaseCommand):
    help = (
        "Exporta usuários (perfil, vínculos e dados brutos) em JSON. "
        "ATENÇÃO: o arquivo contém dados pessoais (CPF, e-mails, nascimento); não compartilhe."
    )

    def add_arguments(self, parser):
        parser.add_argument("usernames", nargs="+", help="Username(s) a exportar.")
        parser.add_argument("-o", "--output", help="Arquivo de saída (padrão: saída padrão).")

    def handle(self, *args, usernames: list[str], output: str | None = None, **options):
        User = get_user_model()
        campo = User.USERNAME_FIELD
        users = {u.get_username(): u for u in User.objects.filter(**{f"{campo}__in": usernames})}
        faltando = [u for u in usernames if u not in users]
        if faltando:
            raise CommandError(f"Usuário(s) não encontrado(s): {', '.join(faltando)}")
        texto = transfer.para_json(transfer.exportar_usuarios(users[u] for u in dict.fromkeys(usernames)))
        if output:
            Path(output).write_text(texto + "\n", encoding="utf-8")
            self.stderr.write(f"{len(users)} usuário(s) exportado(s) para {output}.")
        else:
            self.stdout.write(texto)

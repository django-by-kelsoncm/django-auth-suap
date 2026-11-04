============================
Exportar e Importar Usuários
============================

O módulo ``django_suap_auth.profile`` permite exportar usuários com ``Perfil``, ``Vinculo`` e ``DadosBrutos``
para JSON e importá-los em outro ambiente. O uso típico é reproduzir no ambiente de testes um caso visto em
produção (ex.: regras que dependem de ``suap_raw_data`` e ``suap_vinculos``).

.. warning::
   **Dados pessoais.** O arquivo traz CPF, RG, e-mails, data de nascimento, filiação e a resposta completa do SUAP.
   Use-o só para suporte e testes, não o compartilhe, não o versione e apague-o depois do uso (LGPD).
   A biblioteca não registra o conteúdo em log.

Formato
=======

.. code-block:: json

   {
     "formato": "django-suap-auth/usuarios",
     "versao": 1,
     "exportado_em": "2026-11-04T12:00:00Z",
     "usuarios": [
       {
         "user": {"username": "20231234567", "first_name": "Maria", "last_name": "Aluna",
                  "email": "maria@academico.ifrn.edu.br", "is_active": true},
         "perfil": {"matricula": "20231234567", "cpf": "99988877766", "data_nascimento": "2005-03-01"},
         "vinculos": [{"suap_id": 1, "tipo": "Aluno", "campus": "CNAT", "ativo": true, "detalhamento": {}}],
         "dados_brutos": {"identificacao": "20231234567"}
       }
     ]
   }

- ``user`` leva só ``username``, ``first_name``, ``last_name``, ``email`` e ``is_active``. **Nunca** senha,
  ``is_staff``, ``is_superuser``, grupos ou permissões; a importação recusa esses campos.
- ``perfil`` e cada item de ``vinculos`` trazem todos os campos dos modelos, exceto ``id`` e ``user``.
- ``dados_brutos`` é o ``DadosBrutos.data``.
- ``versao`` muda quando o formato mudar de forma incompatível; a importação recusa versões desconhecidas.
- Também é aceito um único usuário no próprio envelope (``formato``, ``versao``, ``user``, ``perfil``...).

Regras da Importação
====================

A importação é transacional (tudo ou nada) e faz *upsert* por ``username``:

- **User**: usuários novos são criados com senha inutilizável e sem flags de admin; nos existentes são atualizados
  apenas nome, e-mail e ``is_active``. Senha, ``is_staff``, ``is_superuser``, grupos e permissões não mudam.
- **Perfil**: criado ou atualizado com os campos informados; ``perfil`` nulo ou ausente mantém o atual.
- **Vínculos**: substituídos pelos do arquivo (lista vazia ou ausente remove todos).
- **Dados brutos**: substituídos; ``dados_brutos`` nulo ou ausente remove o registro atual.
- Campos desconhecidos (ex.: de uma versão mais nova da biblioteca) são ignorados e listados como avisos.
- Erros de validação indicam a posição exata, ex.: ``usuarios[0].perfil.data_nascimento: ...``.

Django Admin
============

Disponível no ``CustomUserAdmin`` (e em admins que o estendem) **somente para superusuários**:

- Ação **"Exportar (JSON) com perfil, vínculos e dados brutos"** na lista de usuários, que baixa
  ``usuarios-suap-AAAAMMDD-HHMMSS.json``.
- Botão **"Importar usuários"** na lista, que abre ``<admin>/<app>/<user>/importar/``: envie o arquivo, confira a
  prévia (criar/atualizar, perfil, vínculos, dados brutos e avisos) e confirme. Nada é gravado antes da confirmação.
  Limite de 10 MB por arquivo.

Comandos de Gerência
====================

.. code-block:: bash

   # exportar um ou mais usuários (sem -o, escreve na saída padrão)
   python manage.py export_suap_user 20231234567 2080882 -o usuarios.json

   # conferir o que seria feito, sem gravar
   python manage.py import_suap_user usuarios.json --dry-run

   # importar
   python manage.py import_suap_user usuarios.json

API Python
==========

.. code-block:: python

   from django_suap_auth.profile import transfer

   texto = transfer.para_json(transfer.exportar_usuarios(User.objects.filter(username="20231234567")))

   usuarios = transfer.carregar_json(texto)  # levanta transfer.ImportacaoInvalida (atributo .erros)
   resultados = transfer.importar_usuarios(usuarios, dry_run=False)

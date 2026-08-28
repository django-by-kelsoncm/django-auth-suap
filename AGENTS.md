# Requisitos e Lições Aprendidas

- Use o padrão caveman para anotar neste arquivo.
- Manter 100% de cobertura de código em testes unitários (`fail_under = 100` no `pyproject.toml`).
- Executar testes locais via `.venv/bin/pytest`.
- Para gerar migrações do módulo de perfil, usar `.venv/bin/python sandbox/django52/manage.py makemigrations django_suap_auth_profile`.
- Atualizar documentação Sphinx em `docs/` ao alterar modelos ou endpoints. Testar build com `.venv/bin/sphinx-build -b html docs docs/_build/html` sem avisos.
- Atentar ao tamanho de sublinhados em títulos `.rst` para evitar aviso `Title underline too short`.
- Pre-commit hooks rodam `ruff`, `ruff-format` e `pytest`. Garantir arquivos formatados antes de finalizar commit.
- Formato de commit em Português do Brasil, formato conventional detalhado:
  `tipo(escopo): [VERBO] descrição`. Incluir impacto das mudanças, arquivos afetados e motivo. Manter imperativo.
  Verbos: `ADD` (adição), `FIX` (correção), `UPD` (atualização), `DEL` (remoção), `UPG` (atualização de pacotes).
  Tipos: `feat`, `fix`, `refactor`, `style`, `test`, `doc`, `env`, `build`.
- Fluxo de publicação de release:
  1. Criar issue no GitHub (`gh issue create`).
  2. Elevar versão em `pyproject.toml` e `docs/conf.py`.
  3. Criar e testar migrações.
  4. Garantir 100% de cobertura de testes.
  5. Atualizar documentação em `docs/`. Ao criar nova versão (ex: 1.7.0), copiar a versão atual da documentação (`docs/pt-br/<versao-anterior>/` e `docs/en/<versao-anterior>/`) para a nova série (ex: `docs/pt-br/1.7.x/` e `docs/en/1.7.x/`), atualizar o `conf.py` e ajustar os links/redirecionadores em `docs/index.html`.
  6. Commit detalhado com `Closes #issue`.
  7. Push (`git push origin main`).
  8. Criar release no GitHub (`gh release create vX.Y.Z`).
  9. Fechar issue caso não fechada automaticamente.
  10. Registrar o tempo gasto no desenvolvimento na issue correspondente.
- Semgrep GitHub Action: `returntocorp/semgrep-action` obsoleto. Usar `act` para validar.
- release de correcao bug (fix) apenas incrementar versao patch (ex: 1.7.1).
- alteracao apenas em documentacao ou CI nao precisa criar nova release.

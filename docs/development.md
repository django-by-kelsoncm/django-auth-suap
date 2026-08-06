# Desenvolvimento

## Configuração

```bash
git clone https://github.com/kelsoncm/django-suap-auth.git
cd django-suap-auth
uv pip install -e ".[dev]" # ou pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type pre-push
```

## Executando Testes

```bash
pytest --cov=django_suap_auth --cov-report=term-missing
```

## Estilo de Código

```bash
ruff check .
ruff format .
```

## pre-commit

O projeto usa hooks pre-commit:
- **pre-commit**: espaços em branco à direita, fixador de fim de arquivo, verificação yaml, lint/format ruff
- **pre-push**: pytest

## Documentação

```bash
mkdocs serve
```

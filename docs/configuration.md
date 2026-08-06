# Configuração do SUAP OAuth2

## Configuração Básica

No seu `settings.py`:

```python
SUAP_AUTH = {
    'CLIENT_ID': 'seu-client-id',
    'CLIENT_SECRET': 'seu-client-secret',
    'REDIRECT_URI': 'https://sua-aplicacao.com/auth/suap/callback/',
}
```

## Opções de Configuração

| Chave | Padrão | Descrição |
|-------|--------|-----------|
| `CLIENT_ID` | *obrigatório* | ID da aplicação no SUAP |
| `CLIENT_SECRET` | *obrigatório* | Secret da aplicação no SUAP |
| `REDIRECT_URI` | *obrigatório* | URL de callback registrada no SUAP |
| `BASE_URL` | `"https://suap.ifrn.edu.br"` | URL base do servidor SUAP |
| `SCOPES` | `["identificacao", "email"]` | Escopos OAuth2 solicitados |
| `USER_LOOKUP_FIELD` | `"username"` | Campo do modelo `User` usado como chave de busca |
| `USER_ATTR_MAP` | ver abaixo | Dicionário de regras de mapeamento de campos |
| `USER_INFO_FETCHERS` | `["django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher"]` | Lista de fetchers executados na Cadeia de Responsabilidade |
| `USER_INFO_ENDPOINTS` | `["/api/rh/eu/"]` | Lista de endpoints do SUAP a consultar e mesclar |
| `USER_INFO_MAPPERS` | `["django_suap_auth.mappers.DefaultAttrMapUserMapper"]` | Lista de mappers executados na Cadeia de Responsabilidade |
| `USER_JSON_FIELD` | `None` | Campo `JSONField` para gravar a resposta bruta do SUAP |
| `DIRECT_REDIRECT` | `True` | Redirecionamento direto ao SUAP ou página intermediária |
| `CREATE_USER` | `True` | Se `False`, não cria novos usuários e lança exceção |
| `USER_DEFAULTS` | `{"is_active": True}` | Valores atribuídos ao criar um novo usuário |
| `FIRST_USER_DEFAULTS` | `None` | Valores aplicados apenas para o primeiro usuário criado (ex: `{"is_superuser": True, "is_staff": True}`) |
| `UPDATE_FIELDS_ON_CREATE` | `None` | Lista de campos mapeados gravados ao criar (`None` = todos) |
| `UPDATE_FIELDS_ON_LOGIN` | `None` | Lista de campos mapeados sincronizados a cada login (`None` = todos) |
| `BACKEND` | `"django_suap_auth.backends.SuapAuthBackend"` | Caminho da classe backend de autenticação |

---

## Exemplo Completo com Múltiplos Endpoints e Mappers

```python
SUAP_AUTH = {
    'CLIENT_ID': 'seu-client-id',
    'CLIENT_SECRET': 'seu-client-secret',
    'REDIRECT_URI': 'https://sua-aplicacao.com/auth/suap/callback/',
    'USER_INFO_ENDPOINTS': [
        "/api/rh/eu/",
        "/api/rh/meus-dados/",
        {
            "endpoint": "/api/rh/meus-vinculos/",
            "namespace": "vinculos",
            "extract_list": "results",
        },
    ],
    'USER_INFO_MAPPERS': [
        "django_suap_auth.mappers.DefaultAttrMapUserMapper",
        "meu_app.mappers.CustomProfileUserMapper",
    ],
    'USER_ATTR_MAP': {
        "username": "identificacao",
        "email": "email",
        "rg": "rg",
        "cargo": "vinculo.cargo",
        "setor": "vinculo.setor_suap",
        "foto": {
            "key": "url_foto_75x100",
            "transform": "django_suap_auth.transformers.fetch_image_file",
        },
        "is_servidor": lambda info: any(v.get("tipo") == "servidor" for v in info.get("vinculos", [])),
    },
}
```

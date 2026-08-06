# Fetchers (Busca de Dados de Usuário)

O `django-suap-auth` utiliza o padrão **Chain of Responsibility (Cadeia de Responsabilidade)** para buscar e consolidar dados de perfil do usuário a partir de múltiplos endpoints do SUAP ou sistemas externos.

---

## Como Funcionam os Fetchers

Quando o usuário é autenticado via OAuth2, o `access_token` é obtido e a cadeia de fetchers (`USER_INFO_FETCHERS`) é executada em sequência. Cada fetcher recebe o dicionário acumulado `user_info` e pode enriquecê-lo com novos dados.

```
[Access Token] ──> Fetcher 1 (DefaultEndpointsUserInfoFetcher)
                       │ user_info acumulado
                       ▼
                   Fetcher 2 (Fetcher Customizado / LDAP)
                       │ user_info final
                       ▼
                   Cadeia de Mappers
```

---

## Configuração: `USER_INFO_FETCHERS`

No `settings.py`, configure a lista de fetchers em `SUAP_AUTH`:

```python
SUAP_AUTH = {
    "CLIENT_ID": "seu-client-id",
    "CLIENT_SECRET": "seu-client-secret",
    "REDIRECT_URI": "https://sua-app.com/auth/suap/callback/",
    "USER_INFO_FETCHERS": [
        "django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher",
        "meu_app.fetchers.ExternalLdapUserInfoFetcher",
    ],
}
```

---

## Fetcher Padrão: `DefaultEndpointsUserInfoFetcher`

O fetcher padrão consome a lista `USER_INFO_ENDPOINTS` definida em `SUAP_AUTH` e executa requisições HTTP para cada endpoint.

### Formatos de Endpoints Suportados (`USER_INFO_ENDPOINTS`)

#### 1. Endpoint Simples (String)
```python
"USER_INFO_ENDPOINTS": [
    "/api/rh/eu/",
    "/api/rh/meus-dados/",
]
```
Os dados retornados na raiz da resposta JSON são mesclados diretamente na raiz do dicionário `user_info`.

#### 2. Endpoint com Formatação Dinâmica (String com `{chave}`)
```python
"USER_INFO_ENDPOINTS": [
    "/api/rh/eu/",
    "/api/v2/alunos/{matricula}/",
]
```
Chaves entre chaves `{...}` são substituídas pelos valores existentes em `user_info`.

#### 3. Especificação por Dicionário (`dict` spec)
Permite isolar a resposta sob um *namespace*, extrair listas de respostas paginadas ou iterar sobre coleções:

```python
"USER_INFO_ENDPOINTS": [
    "/api/rh/eu/",
    {
        "endpoint": "/api/rh/meus-vinculos/",
        "namespace": "vinculos",   # Injeta sob user_info['vinculos']
        "extract_list": "results", # Extrai do campo paginado 'results'
    },
    {
        "endpoint": "/api/rh/meu-vinculo/{id}/",
        "namespace": "detalhes_vinculos",
        "for_each": "vinculos",    # Itera sobre cada item em user_info['vinculos']
    },
]
```

---

## Criando um Fetcher Customizado

Para criar um fetcher customizado, herde de `BaseUserInfoFetcher` e sobrescreva o método `fetch`:

```python
# meu_app/fetchers.py
from django_suap_auth.fetchers import BaseUserInfoFetcher

class ExternalLdapUserInfoFetcher(BaseUserInfoFetcher):
    """Fetcher que busca informações adicionais no LDAP corporativo a partir do CPF do usuário."""

    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        
        cpf = user_info.get("cpf")
        if cpf:
            # Consulta serviço externo
            user_info["ldap_data"] = meu_servico_ldap.buscar_por_cpf(cpf)
            
        return user_info
```

### Registrando o Fetcher Customizado

```python
# settings.py
SUAP_AUTH = {
    # ...
    "USER_INFO_FETCHERS": [
        "django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher",
        "meu_app.fetchers.ExternalLdapUserInfoFetcher",
    ],
}
```

---

## Funções Utilitárias da API de Fetchers

- `get_user_info_fetchers(cfg=None)`: instancia e retorna a lista de objetos fetchers configurados.
- `run_user_info_fetcher_chain(client, access_token, cfg=None)`: executa toda a cadeia de fetchers e retorna o dicionário `user_info` final.

# Mappers (Mapeamento de Atributos do Usuário)

O `django-suap-auth` utiliza o padrão **Chain of Responsibility (Cadeia de Responsabilidade)** para mapear o dicionário de informações brutos do usuário (`user_info`) obtido pelos fetchers para os campos do modelo `User` do Django.

---

## Como Funcionam os Mappers

A cadeia de mappers (`USER_INFO_MAPPERS`) é executada logo após a conclusão dos fetchers. Cada mapper recebe o dicionário `user_info` acumulado e o dicionário de atributos do modelo `attrs`, podendo adicionar ou modificar pares de campo/valor.

```
[user_info acumulado] ──> Mapper 1 (DefaultAttrMapUserMapper)
                               │ attrs = {'username': '...', 'email': '...'}
                               ▼
                           Mapper 2 (Mapper Customizado / Permissões)
                               │ attrs final
                               ▼
                           SuapAuthBackend (get_or_create)
```

---

## Configuração: `USER_INFO_MAPPERS`

No `settings.py`, configure a lista de mappers em `SUAP_AUTH`:

```python
SUAP_AUTH = {
    # ...
    "USER_INFO_MAPPERS": [
        "django_suap_auth.mappers.DefaultAttrMapUserMapper",
        "meu_app.mappers.ProfileUserMapper",
    ],
}
```

---

## Mapper Padrão: `DefaultAttrMapUserMapper`

O mapper padrão interpreta as regras do dicionário `USER_ATTR_MAP` definido em `SUAP_AUTH`.

### Formatos de Regras em `USER_ATTR_MAP`

#### 1. Mapeamento Direto ou Dotted Path
```python
"USER_ATTR_MAP": {
    "username": "identificacao",
    "email": "email",
    "cargo": "vinculo.cargo",  # extrai do dicionário aninhado user_info['vinculo']['cargo']
}
```

#### 2. Dicionário Bruto Completo (`fulljson`)
```python
"USER_ATTR_MAP": {
    "suap_data": "fulljson",  # atribui o dict user_info inteiro ao campo 'suap_data'
}
```

#### 3. Divisão de Nome em Dois Campos (Tupla)
```python
"USER_ATTR_MAP": {
    ("first_name", "last_name"): "nome_usual",
    # "João Silva Santos" -> first_name="João", last_name="Silva Santos"
}
```

#### 4. Lambdas e Callables Customizados
```python
"USER_ATTR_MAP": {
    "is_staff": lambda info: info.get("tipo_vinculo") == "Servidor",
}
```

#### 5. Especificação com Transformadores e Valores Padrão (`dict` spec)
```python
"USER_ATTR_MAP": {
    "cpf": {
        "key": "cpf",
        "transform": "django_suap_auth.transformers.format_cpf",
    },
    "data_nascimento": {
        "key": "data_nascimento",
        "transform": "django_suap_auth.transformers.parse_date",
    },
    "foto": {
        "key": "url_foto_75x100",
        "transform": "django_suap_auth.transformers.fetch_image_file",
    },
    "status": {
        "key": "situacao",
        "default": "Ativo",
    },
}
```

---

## Transformadores Embutidos (`django_suap_auth.transformers`)

O pacote fornece as seguintes funções de transformação prontas:

| Transformador | Descrição |
|---------------|-----------|
| `fetch_image_file(value, suap_info=None)` | Baixa a imagem da URL e retorna um `ContentFile` para campos `ImageField`/`FileField`. |
| `parse_date(value, suap_info=None)` | Converte string de data ISO (`YYYY-MM-DD`) para `datetime.date`. |
| `format_cpf(value, suap_info=None)` | Formata uma string de 11 dígitos para o padrão `"XXX.XXX.XXX-XX"`. |
| `to_upper(value, suap_info=None)` | Converte valor para maiúsculas. |
| `to_lower(value, suap_info=None)` | Converte valor para minúsculas. |
| `to_bool(value, suap_info=None)` | Converte valor para booleano (`True`/`False`). |

---

## Criando um Mapper Customizado

Para criar um mapper customizado, herde de `BaseUserMapper` (ou de seu alias `BaseSuapUserMapper`) e sobrescreva o método `map_attributes`:

```python
# meu_app/mappers.py
from django_suap_auth.mappers import BaseUserMapper

class CustomProfileUserMapper(BaseUserMapper):
    """Mapper para definir flags de staff e permissões com base no perfil SUAP."""

    def map_attributes(self, user_info, attrs=None):
        attrs = super().map_attributes(user_info, attrs)
        
        # Exemplo: concede permissão de staff para servidores do IFRN
        if user_info.get("tipo_usuario") == "Servidor":
            attrs["is_staff"] = True
            
        return attrs
```

### Registrando o Mapper Customizado

```python
# settings.py
SUAP_AUTH = {
    # ...
    "USER_INFO_MAPPERS": [
        "django_suap_auth.mappers.DefaultAttrMapUserMapper",
        "meu_app.mappers.CustomProfileUserMapper",
    ],
}
```

---

## Funções Utilitárias da API de Mappers

- `get_user_info_mappers(cfg=None)`: instancia e retorna a lista de mappers configurados.
- `run_user_info_mapper_chain(user_info, attr_map=None, cfg=None)`: executa toda a cadeia de mappers e retorna o dicionário `attrs` final para o modelo de usuário.

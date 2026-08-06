# Mapeamento de Atributos do SUAP para o Django User Model

O dicionário `USER_ATTR_MAP` define como os campos retornados pelas APIs do SUAP são gravados no model `User` do Django (seja o padrão ou um customizado via `AUTH_USER_MODEL`).

## Mapeamento Padrão

```python
SUAP_AUTH = {
    # ...
    'USER_ATTR_MAP': {
        'username': 'identificacao',
        'email': 'email',
        ('first_name', 'last_name'): 'nome_usual',
    },
}
```

## Formatos de Mapeamento Suportados

### 1. Campo Simples ou Aninhado (Dotted Path)

```python
'USER_ATTR_MAP': {
    'username': 'identificacao',
    'email': 'email',
    'cpf': 'dados_pessoais.cpf',   # extrai do dicionário aninhado
    'suap_raw': 'fulljson',        # atribui o dicionário user_info completo ao campo
}
```

### 2. Divisão de Nome em Dois Campos (Tupla)

Quando a chave do mapeamento é uma **tupla**, o valor retornado pelo SUAP é dividido no primeiro espaço:

```python
('first_name', 'last_name'): 'nome_usual'
# "João Silva Santos" → first_name="João", last_name="Silva Santos"
# "João"              → first_name="João", last_name=""
```

### 3. Lambdas e Callables Customizadas

Você pode passar um `callable` ou `lambda` que recebe o dicionário completo de informações do SUAP (`suap_user_info`):

```python
'USER_ATTR_MAP': {
    'username': 'identificacao',
    'full_name': lambda info: f"{info.get('primeiro_nome', '')} {info.get('ultimo_nome', '')}".strip(),
    'is_student': lambda info: info.get('tipo_vinculo') == 'Aluno',
}
```

### 4. Dicionários de Especificação com Transformadores e Val padrão (`dict` spec)

Permite definir a chave de origem, valor padrão (`default`) e uma função de transformação (`transform`):

```python
'USER_ATTR_MAP': {
    'username': 'identificacao',
    'cpf': {
        'key': 'cpf',
        'transform': 'django_suap_auth.transformers.format_cpf',
    },
    'data_nascimento': {
        'key': 'data_nascimento',
        'transform': 'django_suap_auth.transformers.parse_date',
    },
    'campus': {
        'key': 'vinculo.campus',
        'default': 'Campus Geral',
    },
}
```

---

## Mapeamento de Fotos (URL vs Download para ImageField)

O SUAP retorna a URL da foto no campo `url_foto_75x100`.

### Caso A: Mapear apenas a URL (CharField / URLField)
```python
'USER_ATTR_MAP': {
    'foto_url': 'url_foto_75x100',
}
```

### Caso B: Baixar a foto e salvar num `ImageField` / `FileField`
Utilize o transformador `fetch_image_file` fornecido pelo pacote:

```python
'USER_ATTR_MAP': {
    'foto': {
        'key': 'url_foto_75x100',
        'transform': 'django_suap_auth.transformers.fetch_image_file',
    },
}
```
Ou via lambda customizada:
```python
from django_suap_auth.transformers import fetch_image_file

'USER_ATTR_MAP': {
    'foto': lambda info: fetch_image_file(info.get('url_foto_75x100')),
}
```

---

## Utilitários de Transformação Embutidos (`django_suap_auth.transformers`)

O pacote já disponibiliza as seguintes funções prontas:

- `fetch_image_file(value, suap_info=None)`: baixa a imagem da URL informada e retorna um `ContentFile` do Django pronto para ser salvo em `ImageField` / `FileField`.
- `parse_date(value, suap_info=None)`: converte string ISO (`YYYY-MM-DD`) para `datetime.date`.
- `format_cpf(value, suap_info=None)`: formata uma string de 11 dígitos para o padrão `"XXX.XXX.XXX-XX"`.
- `to_upper(value, suap_info=None)` / `to_lower(value, suap_info=None)`: converte caixas de texto.
- `to_bool(value, suap_info=None)`: converte valores variados para booleano.

---

## Class-Based Mapper Customizado (`USER_MAPPER`)

Para cenários complexos (como registrar perfis em tabelas vinculadas), você pode implementar uma classe customizada derivada de `BaseSuapUserMapper`:

```python
# mappers.py
from django_suap_auth.mappers import BaseSuapUserMapper

class CustomSuapUserMapper(BaseSuapUserMapper):
    def map_attributes(self, user_info, attr_map=None):
        attrs = super().map_attributes(user_info, attr_map)
        attrs['is_servidor'] = (user_info.get('tipo_vinculo') == 'Servidor')
        return attrs
```

E ativá-la nas configurações do Django:
```python
SUAP_AUTH = {
    # ...
    'USER_MAPPER': 'meu_app.mappers.CustomSuapUserMapper',
}
```

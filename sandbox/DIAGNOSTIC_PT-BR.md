# Guia Detalhado de Troubleshooting - Fluxo de Autenticação

## 🔍 Seu Fluxo Observado

```
1. http://localhost:8000/dashboard/ (acesso protegido)
   ↓ Redireciona para login
2. http://localhost:8000/auth/suap/login/?next=/dashboard/ (página intermediária)
   ↓ POST (clique em "Entrar com SUAP")
3. https://suap.ifrn.edu.br/o/authorize/?response_type=code&client_id=...
   ↓ Login no SUAP + Autorização
4. http://localhost:8000/auth/suap/callback/?code=...&state=... (retorno)
   ↓ PROBLEMA AQUI - retorna para login
5. http://localhost:8000/auth/suap/login/ (volta ao login)
```

**O problema está no PASSO 4 → PASSO 5**: O callback está retornando para login, o que significa que `authenticate()` está retornando `None`.

## ✅ Melhorias Adicionadas

### 1. **Logging Detalhado no Callback**

Agora o arquivo `django_suap_auth/views.py` tem logging em cada etapa:

```
SUAP CALLBACK - Iniciando fluxo
├─ 1. Validando State (CSRF)
├─ 2. Trocando código por token de acesso
├─ 3. Buscando informações do usuário no SUAP
├─ 4. Autenticando usuário no Django
└─ 5. Redirecionando usuário
```

### 2. **View de Debug**

Acesse: `http://localhost:8000/auth/suap/debug/`

Mostra informações em JSON:
- Status de autenticação
- Informações da sessão
- Configurações do SUAP
- Parametros da requisição

## 🚀 Como Diagnosticar Agora

### PASSO 1: Inicie o servidor com output de logs

```bash
cd sandbox/django52
python manage.py runserver
```

O console vai mostrar TODOS os passos da autenticação.

### PASSO 2: Acesse o dashboard

1. Abra http://localhost:8000/dashboard/
2. Você será redirecionado para http://localhost:8000/auth/suap/login/?next=/dashboard/
3. Clique em "Entrar com SUAP"
4. Faça login no SUAP
5. Você será redirecionado para o callback

**IMPORTANTE**: Observe o console do servidor! Você verá exatamente onde falha.

### PASSO 3: Observe os logs do console

Você verá algo como:

```
================================================================================
SUAP CALLBACK - Iniciando fluxo de autenticação
Request path: /auth/suap/callback/
Query string: <QueryDict: {'code': ['...'], 'state': ['...']}>
Session ID: abc123def456
--------------------------------------------------------------------------------
1. Validando State (CSRF)
   State recebido: R1deG3LmL5bYkq-q4rivYr...
   State armazenado: R1deG3LmL5bYkq-q4rivYr...
   ✓ State validado com sucesso
--------------------------------------------------------------------------------
2. Trocando código por token de acesso
   Code recebido: abc123def456...
   ✓ Token obtido com sucesso
   Token data keys: ['access_token', 'token_type', 'expires_in']
   Access token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
--------------------------------------------------------------------------------
3. Buscando informações do usuário no SUAP
   ✓ Informações obtidas com sucesso
   User info keys: ['matricula', 'nome_usual', 'email', ...]
   User info: {'matricula': '12345678', 'nome_usual': 'João Silva', ...}
--------------------------------------------------------------------------------
4. Autenticando usuário no Django
   ✓ Usuário autenticado: 12345678
   ✓ Usuário logado na sessão
--------------------------------------------------------------------------------
5. Redirecionando usuário
   Next URL: /dashboard/
   ✓ Redirecionando para: /dashboard/
================================================================================
```

## 🔴 Se Ver Erro no PASSO 4

Se no passo 4 ver:
```
✗ ERRO: authenticate() retornou None
   Possíveis causas:
   - suap_user_info não contém os campos esperados
   - Mapeamento de usuário não configurado corretamente
   - Backend SUAP não está ativado em AUTHENTICATION_BACKENDS
```

### Causa 1: Campos do SUAP não mapeiam corretamente

**Solução**:
1. Verifique quais campos o SUAP retorna (veja "User info keys" nos logs)
2. Verifique `DEFAULT_USER_ATTR_MAP` em `django_suap_auth/utils.py`
3. Se necessário, customize em `settings.py`:
   ```python
   SUAP_USER_ATTR_MAP = {
       "username": "matricula",  # Deve corresponder ao campo do SUAP
       "email": "email",
       ("first_name", "last_name"): "nome_usual",
   }
   ```

### Causa 2: Backend SUAP não está ativado

**Verificar em `config/settings.py`**:
```python
AUTHENTICATION_BACKENDS = [
    "django_suap_auth.backends.SuapAuthBackend",  # Deve estar aqui!
    "django.contrib.auth.backends.ModelBackend",
]
```

### Causa 3: Permissões insuficientes

Se os scopes solicitados não estão disponíveis para seu usuário SUAP:

**Verificação em `config/settings.py`**:
```python
SUAP_AUTH_SCOPES = ["identificacao", "email"]  # Você tem acesso a esses?
```

**Solução**:
- Ajuste os scopes para apenas os que você tem acesso
- Ou solicite acesso no SUAP

## 🔗 URLs de Debug Disponíveis

Após as mudanças:

- `http://localhost:8000/auth/suap/debug/` - Mostra informações em JSON
- `http://localhost:8000/auth/suap/login/` - Página intermediária de login
- `http://localhost:8000/auth/suap/callback/` - Endpoint de callback

## 📊 Diferença Entre "Permissões no SUAP" vs "Aplicativo"

### Permissões no SUAP
- Você não tem acesso aos dados (ex: seus dados estão bloqueados)
- Solução: Contate administrador do SUAP

### Permissões no Aplicativo
- Seu usuário Django não tem permissão para acessar o `/dashboard/`
- Solução: Adicione permissões no Django
  ```python
  # Em uma view ou shell Django
  from django.contrib.auth.models import User

  user = User.objects.get(username="12345678")
  # Adicione permissões conforme necessário
  ```

## 🎯 Próximos Passos

1. **Reinicie o servidor**: `python manage.py runserver`
2. **Tente fazer login** novamente (navegador limpo/anônimo)
3. **Observe os logs** no console
4. **Copie os logs** completos se houver erro
5. **Compartilhe os logs** comigo para análise detalhada

## ⚠️ Observação Importante

Você mencionou que retorna para `/auth/suap/login/` **depois do callback**. Isso significa:

1. ✅ O SUAP está funcionando
2. ✅ O callback está sendo chamado
3. ❌ Mas `authenticate()` retorna None

Esse é um problema do **mapeamento de usuário** ou **configuração do backend**, não do SUAP em si.

Com os logs detalhados agora disponíveis, você conseguirá diagnosticar exatamente qual campo está faltando ou incorreto.

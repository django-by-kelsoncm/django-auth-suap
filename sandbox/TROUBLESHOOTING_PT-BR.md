# Guia de Troubleshooting - Autenticação SUAP

## Configuração Verificada ✅

A configuração do SUAP foi testada e está **corretamente carregada** nos sandboxes:

```
SUAP_CLIENT_ID: Ca1DUl2YvjC2MACYGKmG1F6UIkxoBdJHiqYl8paX
SUAP_REDIRECT_URI: http://localhost:8000/auth/suap/callback/
SUAP_AUTH_DIRECT_REDIRECT: False (usa página intermediária)
Base URL: https://suap.ifrn.edu.br
Scopes: identificacao, email
```

## Fluxo de Autenticação

1. **Clique em "Entrar com SUAP"** na home page (`http://localhost:8000/`)
2. **Página intermediária** (`/auth/suap/login/`) - clique em "Entrar com SUAP"
3. **Redirecionamento** para o servidor SUAP: `https://suap.ifrn.edu.br/o/authorize/?...`
4. **Autenticação no SUAP** - login com suas credenciais SUAP
5. **Callback** - retorno para `http://localhost:8000/auth/suap/callback/?code=...&state=...`
6. **Validação** - o servidor troca o código pelo token de acesso
7. **Perfil do usuário** - busca informações do perfil no SUAP
8. **Redirecionamento** - para o dashboard (`/dashboard/`)

## Possíveis Problemas e Soluções

### Problema 1: "Credenciais SUAP Inválidas"

**Sintomas:**
- Erro durante login no SUAP
- Mensagem: "Invalid client_id"
- Redirecionamento para login page com mensagem de erro

**Soluções:**

1. **Verifique as credenciais**:
   - Abra `.env` no seu sandbox
   - Confirme que `SUAP_CLIENT_ID` e `SUAP_CLIENT_SECRET` estão corretos
   - Tente registrar um novo aplicativo em: https://suap.ifrn.edu.br/admin/oauth2_provider/application/

2. **Verifique o Redirect URI**:
   - Confirme que `SUAP_REDIRECT_URI=http://localhost:8000/auth/suap/callback/`
   - Deve exatamente corresponder ao registrado no SUAP
   - Sem `/` a mais ou a menos no final

3. **Ambiente correto**:
   - Confirme que está usando o SUAP de produção (suap.ifrn.edu.br)
   - Ou se há um sandbox do SUAP disponível, atualize `SUAP_BASE_URL` em `settings.py`

### Problema 2: "State Mismatch"

**Sintomas:**
- Erro: "Security check failed. Please try logging in again."
- Possível CSRF attack

**Soluções:**

1. **Limpe as cookies**:
   - Abra Developer Tools (F12)
   - Aplicação → Cookies → Limpe todos os cookies de localhost:8000
   - Tente novamente

2. **Verifique as sessões**:
   - Certifique-se que as sessões Django estão ativas
   - O `state` é armazenado na sessão durante o login e validado no callback

3. **Timeouts**:
   - Não deixe um longo intervalo entre clicar em "Login" e confirmar no SUAP
   - A sessão pode expirar

### Problema 3: "Failed to exchange code for token"

**Sintomas:**
- Erro: "Failed to complete login. Please try again."
- Logs mostram erro de token exchange

**Soluções:**

1. **Verifique o CLIENT_SECRET**:
   - Pode ter sido alterado no SUAP
   - Atualize em `.env` e **reinicie o servidor**

2. **Verifique conectividade**:
   - Confirme que pode acessar `https://suap.ifrn.edu.br/o/token/`
   - Teste com: `curl -I https://suap.ifrn.edu.br/o/token/`

3. **Logs detalhados**:
   - Execute o servidor em modo debug
   - Verifique os logs do console para mais detalhes

### Problema 4: "Failed to retrieve user profile"

**Sintomas:**
- Erro: "Failed to retrieve your profile. Please try again."
- Logs mostram erro ao buscar informações do usuário

**Soluções:**

1. **Verifique os scopes**:
   - Confirme que os scopes solicitados estão corretos
   - Em `settings.py`: `SUAP_AUTH_SCOPES = ["identificacao", "email"]`
   - Verifique se o usuário SUAP tem acesso a esses dados

2. **Verifique o token de acesso**:
   - O token pode ter expirado
   - Tente fazer login novamente

3. **Endpoint do SUAP**:
   - Confirme que o endpoint `/api/rh/eu/` está disponível
   - Teste manualmente com curl usando o token de acesso

## Depuração

### 1. Execute o script de teste

```bash
cd sandbox/django52
python test_suap_config.py
```

Isso verificará:
- Variáveis de ambiente
- Configurações Django
- URL de autorização gerada

### 2. Ative logs detalhados

Os sandboxes já têm logging configurado. Execute o servidor e verifique o console:

```bash
cd sandbox/django52
python manage.py runserver
```

Você verá logs da autenticação SUAP no console.

### 3. Teste a URL de autorização manualmente

Na homepage, você verá um debug card com as configurações SUAP.

### 4. Use as Django Developer Tools

No DEBUG mode, você pode inspecionar:
- Variáveis de sessão
- Cookies
- Requisições HTTP

## Informações Úteis

- **Documentação SUAP OAuth2**: https://suap.ifrn.edu.br/api/v2/docs/
- **Registro de aplicativos**: https://suap.ifrn.edu.br/admin/oauth2_provider/application/
- **Sandbox oficial**: https://suap.ifrn.edu.br (não há sandbox separado)

## Próximos Passos

Se ainda assim não conseguir:

1. Verifique se o `SUAP_CLIENT_ID` está ativo no SUAP
2. Confirme que o usuário testado tem acesso ao SUAP
3. Verifique se há restrições de rede/firewall
4. Consulte a equipe do SUAP para suporte

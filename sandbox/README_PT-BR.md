# Django SUAP Auth - Sandboxes

Este diretório contém dois sandboxes (ambientes de teste) para o pacote `django-suap-auth`:

- **django52**: Django 5.2 (versão mais recente)
- **django60**: Django 6.0 (próxima versão)

## Pré-requisitos

- Python 3.13+
- Ambiente virtual ativado (`.venv`)
- Pacotes instalados: `pip install -r requirements.txt`

## Iniciando o Servidor

### Django 5.2

```bash
cd sandbox/django52
python manage.py migrate  # Primeira execução
python manage.py runserver
```

Acesse em: http://localhost:8000

### Django 6.0

```bash
cd sandbox/django60
python manage.py migrate  # Primeira execução
python manage.py runserver 8001
```

Acesse em: http://localhost:8000

## Configuração SUAP

As credenciais do SUAP estão no arquivo `.env` de cada sandbox:

```
SUAP_CLIENT_ID=Ca1DUl2YvjC2MACYGKmG1F6UIkxoBdJHiqYl8paX
SUAP_CLIENT_SECRET=vjVbcwjHYDcs5ilSjesqROxdxm1Gndd3HiwTpjS7xQuwx5SgcRqABpzVeOjvcwHw3luZ4swCuOvHsyec2jtLpE46j4tBQcMEqSoUH236xhdkfv51KcEZHZtnjPnJhcVg
SUAP_REDIRECT_URI=http://localhost:8000/auth/suap/callback/
SUAP_AUTH_DIRECT_REDIRECT=False
```

**Nota**: Após alterar o `.env`, **reinicie o servidor Django** para que as mudanças tenham efeito.

## Fluxo de Autenticação

1. Acesse http://localhost:8000/ (página pública)
2. Clique em **"Entrar com SUAP"**
3. Na página de login intermediária, clique em **"Entrar com SUAP"** novamente
4. Você será redirecionado para o servidor SUAP em https://suap.ifrn.edu.br
5. Faça login com suas credenciais SUAP (incluindo segundo fator se aplicável)
6. Autorize o acesso aos dados solicitados
7. Você será redirecionado de volta para o dashboard (/dashboard/)
8. Seu usuário será criado/atualizado no Django automaticamente

## Páginas Disponíveis

### Públicas

- **/** (Home) - Página de boas-vindas com informações sobre o fluxo OAuth2
  - Mostra status de autenticação
  - Exibe configurações SUAP (debug)
  - Links para login ou dashboard

### Protegidas (requer autenticação)

- **/dashboard/** - Painel do usuário autenticado
  - Exibe informações do usuário
  - Mostra dados de autenticação SUAP
  - Link para logout

### Sistema de Autenticação

- **/auth/suap/login/** - Página intermediária de login (pode ser pulada com SUAP_AUTH_DIRECT_REDIRECT=True)
- **/auth/suap/callback/** - Endpoint de retorno do SUAP (automático)
- **/logout/** - Desconexão

## Scripts de Teste e Debug

### Verificar Configuração

```bash
cd sandbox/django52
python test_suap_config.py
```

Mostra:
- Variáveis de ambiente carregadas
- Configurações Django
- Configurações internas do SUAP
- URL de autorização de teste

### Testar Fluxo de Autenticação

```bash
cd sandbox/django52
python test_auth_flow.py
```

Mostra:
- Conectividade com SUAP
- Verificação de credenciais
- Instruções passo-a-passo para testar

## Troubleshooting

Se encontrar problemas na autenticação:

1. **Leia**: `TROUBLESHOOTING_PT-BR.md` no diretório sandbox
2. **Verifique**: `.env` tem credenciais SUAP válidas
3. **Reinicie**: O servidor Django após alterar `.env`
4. **Limpe**: Cookies do navegador (F12 → Application → Cookies)
5. **Teste**: Execute os scripts de teste
6. **Debug**: Ative logging (já está configurado em DEBUG mode)

## Estrutura de Diretórios

```
sandbox/
├── TROUBLESHOOTING_PT-BR.md      # Guia de troubleshooting
├── django52/
│   ├── .env                       # Configurações (NÃO versione)
│   ├── db.sqlite3                # Banco de dados SQLite
│   ├── manage.py                 # Gerenciador Django
│   ├── requirements.txt           # Dependências
│   ├── test_suap_config.py        # Script de teste de config
│   ├── test_auth_flow.py          # Script de teste de fluxo
│   ├── config/
│   │   ├── settings.py            # Configurações Django
│   │   ├── urls.py                # Rotas
│   │   └── wsgi.py                # WSGI
│   └── home/
│       ├── views.py               # Views (home, dashboard)
│       ├── urls.py                # Rotas da app home
│       └── templates/
│           └── home/
│               ├── base.html      # Template base com Bootstrap
│               ├── home.html      # Home page
│               └── dashboard.html # Dashboard
└── django60/
    └── (mesma estrutura do django52)
```

## Dependências

Veja `requirements.txt` em cada sandbox para a lista completa. Principais:

- Django 5.2+ ou 6.0+
- django-suap-auth (editable install do pacote local)
- requests

## Ambiente de Desenvolvimento

O DEBUG mode está ativado (veja `.env`), então:

- Mensagens de erro detalhadas são exibidas
- Reloading automático ao modificar código
- Logging detalhado do django-suap-auth no console

**NUNCA deixe DEBUG=True em produção!**

## Notas Importantes

- As credenciais SUAP no `.env` são **para desenvolvimento apenas**
- A sessão Django usa SQLite (não persistente entre reinicializações)
- CSRF protection está ativada
- Cookies de sessão são HttpOnly por segurança
- O redirect intermediário (SUAP_AUTH_DIRECT_REDIRECT=False) é útil para debug

## Suporte

Para problemas:

1. Consulte `TROUBLESHOOTING_PT-BR.md`
2. Execute os scripts de teste
3. Verifique os logs do console (DEBUG mode)
4. Limpe cookies e cookies do navegador
5. Reinicie o servidor Django

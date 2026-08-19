===========================
Configuração do SUAP OAuth2
===========================

Configuração Básica
===================

No seu ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'seu-client-id',
       'CLIENT_SECRET': 'seu-client-secret',
       'REDIRECT_URI': 'https://sua-aplicacao.com/auth/suap/callback/',
   }

Opções de Configuração
======================

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Chave
     - Padrão
     - Descrição
   * - ``CLIENT_ID``
     - *obrigatório*
     - ID da aplicação no SUAP
   * - ``CLIENT_SECRET``
     - *obrigatório*
     - Secret da aplicação no SUAP
   * - ``REDIRECT_URI``
     - *obrigatório*
     - URL de callback registrada no SUAP
   * - ``BASE_URL``
     - ``"https://suap.ifrn.edu.br"``
     - URL base do servidor SUAP
   * - ``SCOPES``
     - ``["identificacao", "email"]``
     - Escopos OAuth2 solicitados
   * - ``USER_LOOKUP_FIELD``
     - ``"username"``
     - Campo do modelo ``User`` usado como chave de busca
   * - ``USER_ATTR_MAP``
     - ver :doc:`attribute-mapping`
     - Dicionário de regras de mapeamento de campos
   * - ``USER_INFO_FETCHERS``
     - ``["django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher"]``
     - Lista de fetchers executados na Cadeia de Responsabilidade
   * - ``USER_INFO_ENDPOINTS``
     - ``["/api/rh/eu/"]``
     - Lista de endpoints do SUAP a consultar e mesclar
   * - ``USER_INFO_MAPPERS``
     - ``["django_suap_auth.mappers.DefaultAttrMapUserMapper"]``
     - Lista de mappers executados na Cadeia de Responsabilidade
   * - ``USER_JSON_FIELD``
     - ``None``
     - Campo ``JSONField`` para gravar a resposta bruta do SUAP
   * - ``DIRECT_REDIRECT``
     - ``True``
     - Redirecionamento direto ao SUAP ou página intermediária
   * - ``CREATE_USER``
     - ``True``
     - Se ``False``, não cria novos usuários e lança exceção
   * - ``USER_DEFAULTS``
     - ``{"is_active": True}``
     - Valores atribuídos ao criar um novo usuário
   * - ``FIRST_USER_DEFAULTS``
     - ``{"is_staff": True, "is_superuser": True}``
     - Valores adicionais aplicados apenas ao primeiro usuário criado no banco de dados.
   * - ``UPDATE_FIELDS_ON_CREATE``
     - ``None``
     - Lista de campos mapeados gravados ao criar (``None`` = todos)
   * - ``UPDATE_FIELDS_ON_LOGIN``
     - ``None``
     - Lista de campos mapeados sincronizados a cada login (``None`` = todos)
   * - ``BACKEND``
     - ``"django_suap_auth.backends.SuapAuthBackend"``
     - Caminho da classe backend de autenticação

Exemplo Completo com Múltiplos Endpoints e Mappers
==================================================

.. code-block:: python

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

Controle de Criação de Usuários
===============================

Por padrão, a biblioteca cria automaticamente um usuário no Django no primeiro login efetuado via SUAP. Esse comportamento é totalmente configurável:

1. Desabilitar Criação Automática via Configuração
--------------------------------------------------

Se a opção ``CREATE_USER`` for definida como ``False``, o login será negado para usuários que não possuem conta local previamente cadastrada no Django, lançando a exceção ``django_suap_auth.exceptions.SuapUserNotAllowedError``:

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'seu-client-id',
       'CLIENT_SECRET': 'seu-client-secret',
       'REDIRECT_URI': 'https://sua-aplicacao.com/auth/suap/callback/',
       'CREATE_USER': False,  # Impede cadastro automático no login
   }

2. Primeiro Usuário como Superusuário (`FIRST_USER_DEFAULTS`)
-------------------------------------------------------------

Por padrão, se nenhum usuário existir no banco de dados no momento do primeiro login, o primeiro usuário criado receberá automaticamente ``is_staff = True`` e ``is_superuser = True`` (através de ``FIRST_USER_DEFAULTS = {"is_staff": True, "is_superuser": True}``).

Caso deseje desabilitar essa promoção automática do primeiro usuário, defina a chave como ``None`` em seu ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       'CLIENT_ID': 'seu-client-id',
       'CLIENT_SECRET': 'seu-client-secret',
       'REDIRECT_URI': 'https://sua-aplicacao.com/auth/suap/callback/',
       'FIRST_USER_DEFAULTS': None,  # O primeiro usuário criado não será superuser/staff
   }

3. Decisão Dinâmica via Backend Customizado
-------------------------------------------

Para aplicar regras condicionais dinâmicas durante o login (por exemplo, autorizar o cadastro apenas para servidores ou determinados vínculos), herde de ``SuapAuthBackend`` ou ``SuapProfileAuthBackend`` e sobrescreva o método ``get_or_create_user`` ou ``create_user``:

.. code-block:: python

   from django_suap_auth.profile.backends import SuapProfileAuthBackend
   from django_suap_auth.exceptions import SuapUserNotAllowedError

   class CustomSuapAuthBackend(SuapProfileAuthBackend):
       def get_or_create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
           raw_info = mapped_attrs.get("suap_data", {})
           # Exemplo: só permite criação automática se o usuário for Servidor
           if raw_info.get("tipo_vinculo") != "Servidor":
               raise SuapUserNotAllowedError("Cadastro automático permitido apenas para servidores.")

           return super().get_or_create_user(lookup_field, lookup_value, mapped_attrs, cfg)

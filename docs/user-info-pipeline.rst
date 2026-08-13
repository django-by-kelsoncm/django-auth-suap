======================================================
Pipeline de Busca e Mapeamento do Perfil do Usuário
======================================================

O ``django-suap-auth`` utiliza o padrão de projeto **Chain of Responsibility (Cadeia de Responsabilidade)** para os subsistemas de busca de dados (``USER_INFO_FETCHERS``) e mapeamento de atributos (``USER_INFO_MAPPERS``).

Arquitetura Geral
=================

.. code-block:: text

   1. OAuth2 Code Swap ──> Access Token
                                │
                                ▼
   2. USER_INFO_FETCHERS Chain ──> Dicionário user_info acumulado
                                │
                                ▼
   3. USER_INFO_MAPPERS Chain  ──> Dicionário attrs para o Django Model
                                │
                                ▼
   4. User Model (get_or_create) ──> Usuário Autenticado

1. Cadeia de Busca de Dados (``USER_INFO_FETCHERS``)
====================================================

O SUAP possui múltiplos endpoints de API (``/api/rh/eu/``, ``/api/rh/meus-dados/``, ``/api/rh/meus-vinculos/``). A cadeia de fetchers é responsável por consultar esses endpoints e mesclar as informações em um único dicionário ``user_info``.

Elo Padrão: ``DefaultEndpointsUserInfoFetcher``
------------------------------------------------

Consome a lista ``USER_INFO_ENDPOINTS`` do ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       # Lista de endpoints do SUAP a serem consultados e mesclados
       "USER_INFO_ENDPOINTS": [
           "/api/rh/eu/",          # Dados básicos na raiz do dict
           "/api/rh/meus-dados/",  # Mescla rg, filiação, vinculo.cargo, etc.
           {
               "endpoint": "/api/rh/meus-vinculos/",
               "namespace": "vinculos",   # Injeta sob user_info['vinculos']
               "extract_list": "results", # Extrai a lista do campo paginado 'results'
           },
           {
               "endpoint": "/api/rh/meu-vinculo/{id}/",
               "namespace": "detalhes_vinculos",
               "for_each": "vinculos",    # Itera sobre cada item em user_info['vinculos']
           },
       ],
   }

Criando um Fetcher Customizado para Fontes Externas
---------------------------------------------------

Você pode adicionar elos à cadeia ``USER_INFO_FETCHERS`` para consultar sistemas de RH internos, LDAP ou bancos corporativos:

.. code-block:: python

   # meu_app/fetchers.py
   from django_suap_auth.fetchers import BaseUserInfoFetcher

   class ExternalLdapUserInfoFetcher(BaseUserInfoFetcher):
       def fetch(self, client, access_token, user_info=None):
           user_info = super().fetch(client, access_token, user_info)
           
           cpf = user_info.get("cpf")
           if cpf:
               # Enriquece o dicionário com dados de outra fonte
               user_info["ldap"] = meu_servico_ldap.buscar_por_cpf(cpf)
               
           return user_info

Configuração no ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       "USER_INFO_FETCHERS": [
           "django_suap_auth.fetchers.DefaultEndpointsUserInfoFetcher",
           "meu_app.fetchers.ExternalLdapUserInfoFetcher",
       ],
   }

2. Cadeia de Mapeamento (``USER_INFO_MAPPERS``)
===============================================

Após a busca, a cadeia de mappers recebe o ``user_info`` unificado e constrói os atributos do modelo de usuário do Django.

Elo Padrão: ``DefaultAttrMapUserMapper``
----------------------------------------

Aplica as regras configuradas no ``USER_ATTR_MAP``:

.. code-block:: python

   SUAP_AUTH = {
       "USER_INFO_MAPPERS": [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
       ],
       "USER_ATTR_MAP": {
           "username": "identificacao",
           "email": "email",
           "rg": "rg",
           "cargo": "vinculo.cargo",
           "foto": {
               "key": "url_foto_75x100",
               "transform": "django_suap_auth.transformers.fetch_image_file",
           },
           "is_servidor": lambda info: any(v.get("tipo") == "servidor" for v in info.get("vinculos", [])),
       },
   }

Criando um Mapper Customizado
-----------------------------

Para adicionar lógica complexa ou manipular o modelo de usuário diretamente:

.. code-block:: python

   # meu_app/mappers.py
   from django_suap_auth.mappers import BaseUserMapper

   class ProfileUserMapper(BaseUserMapper):
       def map_attributes(self, user_info, attrs=None):
           attrs = super().map_attributes(user_info, attrs)
           if user_info.get("ldap", {}).get("is_admin"):
               attrs["is_staff"] = True
           return attrs

Configuração no ``settings.py``:

.. code-block:: python

   SUAP_AUTH = {
       "USER_INFO_MAPPERS": [
           "django_suap_auth.mappers.DefaultAttrMapUserMapper",
           "meu_app.mappers.ProfileUserMapper",
       ],
   }

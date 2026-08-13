================
django-suap-auth
================

Backend de autenticação OAuth2 do Django para **SUAP** (Sistema Unificado de Administração Pública), o sistema de gestão acadêmica do IFRN.

.. toctree::
   :maxdepth: 2
   :caption: Sumário de Conteúdos:

   installation
   configuration
   scopes
   attribute-mapping
   user-info-pipeline
   fetchers
   mappers
   auth-flow
   sandboxes
   development
   release

Funcionalidades
===============

- Fluxo de autorização de código OAuth2 com SUAP
- Escopos configuráveis (``identificacao``, ``email``, ``documentos_pessoais``, ``dados_academicos``, ``dados_pessoais``, ``reitoria``)
- Mapeamento flexível de atributos da resposta SUAP para campos do modelo de usuário do Django
- Armazenamento opcional em campo JSON para a resposta completa do SUAP
- Página de login intermediária configurável (``SUAP_AUTH['DIRECT_REDIRECT']``)
- Proteção CSRF via validação do parâmetro de estado

Links Rápidos
=============

- :doc:`Instalação <installation>`
- :doc:`Configuração <configuration>`
- :doc:`Escopos <scopes>`
- :doc:`Mapeamento de atributos <attribute-mapping>`
- :doc:`Pipeline de perfil de usuário <user-info-pipeline>`
- :doc:`Fetchers (Busca de dados) <fetchers>`
- :doc:`Mappers (Mapeamento) <mappers>`
- :doc:`Fluxo de autenticação <auth-flow>`
- :doc:`Sandboxes <sandboxes>`
- :doc:`Desenvolvimento <development>`
- :doc:`Processo de Release <release>`

================
django-suap-auth
================

Backend de autenticação OAuth2 do Django para **SUAP** (Sistema Unificado de Administração Pública), o sistema de gestão acadêmica do IFRN.

Introdução
==========

O **django-suap-auth** é uma biblioteca Python/Django projetada para simplificar e padronizar a integração de autenticação e a obtenção de dados de usuários entre aplicações Django e o **SUAP** (Sistema Unificado de Administração Pública) — a plataforma de gestão acadêmica e administrativa utilizada pelo Instituto Federal do Rio Grande do Norte (IFRN).

O pacote abstrai a complexidade da comunicação via protocolo **OAuth2 (Authorization Code Flow)** com o provedor de identidade do SUAP, realizando automaticamente a troca de códigos por tokens de acesso, a consulta das APIs de dados do usuário e o mapeamento dessas informações para o modelo de usuário do Django (``User``).

Além do fluxo básico de login, a biblioteca fornece:

* **Pipeline Extensível de Dados**: Arquitetura baseada no padrão *Chain of Responsibility* com *fetchers* e *mappers* customizáveis para consultar diferentes endpoints da API do SUAP e mapear atributos diretamente para o modelo de usuário.
* **Módulo de Perfil e Dados Brutos (``django_suap_auth.profile``)**: Modelos Django prontos (``Perfil``, ``DadosBrutos``, ``Vinculo``) para armazenar os vínculos acadêmicos/servidores e guardar a resposta completa do SUAP em formato JSON.
* **Autenticação JWT Nativa (``django_suap_auth.jwt``)**: Endpoints integrados para emissão e validação de tokens JWT (sem necessidade de frameworks REST externos).
* **Personificação de Usuários (``django_suap_auth.impersonation`` / impersonate)**: Suporte a workflows de testes e suporte através da troca temporária de identidade de usuários.

Funcionalidades
===============

- Fluxo de autorização de código OAuth2 com SUAP
- Entrypoints opcionais para autenticação JWT (``/api/token/pair``, ``/api/token/refresh``, ``/api/token/verify``)
- Submódulo ``django_suap_auth.profile`` com modelos de perfil prontos (``Perfil``, ``DadosBrutos``, ``Vinculo``)
- Submódulo ``django_suap_auth.impersonation`` para troca temporária de identidade de usuário
- Escopos configuráveis (``identificacao``, ``email``, ``documentos_pessoais``, ``dados_academicos``, ``dados_pessoais``, ``reitoria``)
- Mapeamento flexível de atributos da resposta SUAP para campos do modelo de usuário do Django
- Armazenamento opcional em campo JSON para a resposta completa do SUAP
- Página de login intermediária configurável (``SUAP_AUTH['DIRECT_REDIRECT']``)
- Proteção CSRF via validação do parâmetro de estado

.. toctree::
   :maxdepth: 2
   :caption: Sumário de Conteúdos:

   installation
   configuration
   profile-models
   impersonation
   jwt-endpoints
   scopes
   attribute-mapping
   user-info-pipeline
   fetchers
   mappers
   auth-flow
   sandboxes
   development
   release

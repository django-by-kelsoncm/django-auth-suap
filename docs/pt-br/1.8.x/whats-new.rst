================
O Que Há de Novo
================

Esta página resume as novidades e melhorias introduzidas na série **1.8.x** do ``django-suap-auth``.

.. note::
   Esta página deve ser atualizada a cada nova release publicada.

Versão 1.8.6
============

- **Expansão de Tamanhos de Campos de Perfil e Auditoria**: Expandido o tamanho limite (``max_length``) dos campos dos modelos de perfil, auditoria e erros (de 10/50/100 para 256) para evitar falha ``DataError`` ao receber valores mais longos retornados pelas APIs do SUAP (ex: sexo "PREFERE NÃO INFORMAR", tipo sanguíneo "NÃO INFORMADO").
- **Filtragem de Notificações ao Sentry para Status HTTP 404 e 403**: Atualizado o serviço ``report_sync_error_to_sentry`` para ignorar erros HTTP 404 (Não Encontrado) e 403 (Proibido) em buscas secundárias, evitando falsos alertas de exceção no Sentry quando endpoints opcionais não contêm dados para determinados usuários.

Versão 1.8.5
============

- **Tratamento de Erros em Fetchers Secundários**: Corrigida a tolerância a falhas na busca de dados do usuário via fetchers e endpoints do SUAP. Erros em endpoints secundários registram o erro em ``_sync_errors`` e permitem a conclusão do login, interrompendo o fluxo apenas se a falha ocorrer no endpoint primário de identificação (``/api/rh/eu/``).

Versão 1.8.4
============

- **Internacionalização em Holandês (``nl``)**: Adicionado suporte a internacionalização no código para o idioma Holandês (catálogos de tradução ``.po``/``.mo`` para ``nl``).

Versão 1.8.3
============

- **Configurações de Alertas de Auditoria**: Externalizados os limiares de regras de alertas de segurança para o ``settings.py`` através das configurações ``SUAP_AUTH_AUDIT_*``.

Versão 1.8.2
============

- **Atalho no Django Admin**: Adicionado botão de atalho para o Dashboard de Auditoria diretamente na tela de listagem de Eventos de Auditoria do Django Admin.

Versão 1.8.1
============

- **Resiliência e Migração**: Adicionado tratamento tolerante a falhas no registro de auditoria e atualizadas as migrações nos sandboxes.

Versão 1.8.0
============

- **Novo Módulo de Auditoria (``django_suap_auth.audit``)**:
  - Trilha de auditoria para capturar eventos de autenticação, trocas de tokens e acessos.
  - Dashboard interativo integrado ao Django Admin.
  - Sinais e suporte a monitoramento de segurança.

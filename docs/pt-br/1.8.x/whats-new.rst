================
O Que Há de Novo
================

Esta página resume as novidades e melhorias introduzidas na série **1.8.x** do ``django-suap-auth``.

.. note::
   Esta página deve ser atualizada a cada nova release publicada.

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

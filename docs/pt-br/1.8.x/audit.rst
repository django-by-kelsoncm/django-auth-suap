=====================================
Trilha de Auditoria e Dashboard Admin
=====================================

O sub-módulo ``django_suap_auth.audit`` fornece uma trilha de auditoria (*audit trail*) centralizada e em conformidade com a LGPD, Marco Civil da Internet e normas do TCU/CGU.

Recursos Principais
===================

* **Eventos de Autenticação e Impersonate**: Registro automático de logins SUAP (sucesso/falha), emissão/renovação de JWT e sessões de impersonate.
* **Integração com APIs (Django Ninja / DRF)**: Captura de acessos a endpoints protegidos com medição de tempo de execução (``duration_ms``) e código HTTP.
* **Identificador de Correlação (Correlation ID)**: Injeção automática do cabeçalho ``X-Correlation-ID`` para rastreabilidade de fluxos.
* **Governança LGPD e Pseudonimização**: Registro de IP original bruto com permissão restrita (``django_suap_auth_audit.view_raw_ip``) e gravação de IP em hash SHA-256 para estatísticas públicas.
* **Retenção de 5 Anos**: Suporte a arquivamento comprimido em cold storage via comando ``python manage.py audit_archive``.
* **Dashboard no Django Admin**: Painel visual nativo com suporte a Tema Claro (*Light Mode*) e Tema Escuro (*Dark Mode*).
* **Alertas Automáticos**: Regras para detecção de picos de falha, impersonate fora de horário e erros 401/403 em APIs, com notificações via Admin, E-mail, Webhook e Telegram.

Configuração
============

Para ativar a auditoria, adicione ``django_suap_auth.audit`` ao seu ``INSTALLED_APPS`` e configure o middleware:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "django_suap_auth",
        "django_suap_auth.audit",
    ]

    MIDDLEWARE = [
        "django_suap_auth.audit.middleware.CorrelationMiddleware",
        "django_suap_auth.audit.middleware.AuditMiddleware",
        # ...
    ]

Comando de Arquivamento
=======================

Para exportar registros com mais de 365 dias para arquivos comprimidos JSONL e manter a tabela relacional limpa:

.. code-block:: bash

    python manage.py audit_archive --days=365 --output=/caminho/backup.jsonl.gz

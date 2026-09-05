================
O Que Há de Novo
================

Esta página resume as novidades e melhorias introduzidas na série **1.8.x** do ``django-suap-auth``.

.. note::
   Esta página deve ser atualizada a cada nova release publicada.

Versão 1.8.9
============

- **Página de Acesso Negado para Usuário Autenticado sem Permissão**: A ``SuapLoginView`` agora detecta quando é acessada por um usuário já autenticado (sinal de que uma verificação de permissão em outra página falhou, como o ``has_permission`` do Django Admin) e, em vez de reiniciar o fluxo OAuth2 — criando um loop confuso de login —, exibe uma página informando que o usuário está logado mas não tem permissão para o recurso solicitado. Personalizável via o atributo ``access_denied_template``.

Versão 1.8.8
============

- **Notificação do Sentry com Nível ``info`` para Falhas de Sincronização Secundária**: As notificações enviadas ao Sentry durante erros de busca secundária de dados no SUAP agora utilizam o nível de severidade ``info`` em vez de ``error``, evitando alertas de erro/bug para falhas não-críticas que não impedem a conclusão do login.

Versão 1.8.7
============

- **Persistência Prioritária de DadosBrutos**: Alterado o fluxo de sincronização do perfil (`sync_suap_profile`) para salvar o modelo `DadosBrutos` antes de tentar manipular ou salvar os modelos `Perfil` e `Vinculo`, garantindo que os dados brutos recebidos do SUAP fiquem salvos mesmo em caso de falha de persistência no perfil.

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

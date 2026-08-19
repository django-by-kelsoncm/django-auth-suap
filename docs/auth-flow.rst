=====================
Fluxo de Autenticação
=====================

Visão Geral
===========

``django-suap-auth`` implementa o fluxo de autorização de código OAuth2.

.. mermaid::
   :caption: Fluxo de autenticação via SUAP
   :alt: Diagrama do fluxo de login e autenticação via SUAP

   flowchart TD
       A["Usuário"] -->|Clica em Entrar| B["GET /auth/suap/login/"]
       B -->|Gera state| C["Armazena state na sessao"]
       C -->|DIRECT_REDIRECT true| D["Redireciona para SUAP"]
       C -->|DIRECT_REDIRECT false| E["Renderiza login.html"]
       E -->|Clica botao| D
       D -->|Faz login| F["SUAP /o/authorize/"]
       F -->|Autoriza| G["Redireciona com code"]
       G -->|POST /auth/suap/callback/| H["Valida state"]
       H -->|Valido| I["POST /o/token/"]
       H -->|Invalido| J["Erro CSRF"]
       I -->|Troca code por token| K["Recebe access_token"]
       K -->|GET /api/rh/eu/| L["SUAP API"]
       L -->|Dados do usuario| M["Informacoes JSON"]
       M -->|authenticate| N["Backend SUAP"]
       N -->|Cria Usuario| O["Usuario autenticado"]
       O -->|login| P["Sessao criada"]
       P -->|Redireciona| Q["LOGIN_REDIRECT_URL"]
       Q -->|Ex /dashboard/| R["Logado com sucesso"]

Redirecionamento Direto (Padrão)
================================

Com ``DIRECT_REDIRECT = True`` (padrão em ``SUAP_AUTH``), o usuário é imediatamente redirecionado para o SUAP quando visita ``/auth/suap/login/``.

Página Intermediária
====================

Com ``DIRECT_REDIRECT = False`` em ``SUAP_AUTH``, a view de login renderiza uma página intermediária (``django_suap_auth/login.html``) onde o usuário deve clicar em um botão para prosseguir para o SUAP.

Proteção CSRF
=============

O parâmetro de estado é gerado usando ``secrets.token_urlsafe(32)`` e armazenado na sessão. Ele é validado no callback para prevenir ataques CSRF.

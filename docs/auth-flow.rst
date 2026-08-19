=====================
Fluxo de Autenticação
=====================

Visão Geral
===========

``django-suap-auth`` implementa o fluxo de autorização de código OAuth2.


.. figure:: auth-flow.svg
   :alt: Fluxo de autenticação via SUAP
   :align: center
   :width: 100%

   Fluxo de autenticação via SUAP

Redirecionamento Direto (Padrão)
================================

Com ``DIRECT_REDIRECT = True`` (padrão em ``SUAP_AUTH``), o usuário é imediatamente redirecionado para o SUAP quando visita ``/auth/suap/login/``.

Página Intermediária
====================

Com ``DIRECT_REDIRECT = False`` em ``SUAP_AUTH``, a view de login renderiza uma página intermediária (``django_suap_auth/login.html``) onde o usuário deve clicar em um botão para prosseguir para o SUAP.

Proteção CSRF
=============

O parâmetro de estado é gerado usando ``secrets.token_urlsafe(32)`` e armazenado na sessão. Ele é validado no callback para prevenir ataques CSRF.

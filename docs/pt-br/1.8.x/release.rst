======================
Processo de Lançamento
======================

Versionamento
=============

Este projeto segue `Versionamento Semântico <https://semver.org/>`_.

Etapas
======

1. Atualizar ``version`` em ``pyproject.toml``
2. Atualizar a seção O Que Há de Novo (``whats-new.rst``) e o changelog
3. Criar uma tag git: ``git tag v1.8.x``
4. Enviar a tag: ``git push origin v1.8.x``
5. O workflow ``publish.yml`` do GitHub Actions publicará automaticamente no PyPI via Trusted Publisher

Trusted Publisher
=================

A publicação no PyPI usa `Trusted Publisher <https://docs.pypi.org/trusted-publishers/>`_ do GitHub Actions — nenhum segredo necessário.

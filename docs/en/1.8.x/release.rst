===============
Release Process
===============

Versioning
==========

This project follows `Semantic Versioning <https://semver.org/>`_.

Steps
=====

1. Update ``version`` in ``pyproject.toml``
2. Update changelog
3. Create a git tag: ``git tag v1.6.0``
4. Push tag: ``git push origin v1.6.0``
5. GitHub Actions ``publish.yml`` workflow will automatically publish to PyPI via Trusted Publisher

Trusted Publisher
=================

PyPI publishing uses GitHub Actions `Trusted Publisher <https://docs.pypi.org/trusted-publishers/>`_ — no secrets required.

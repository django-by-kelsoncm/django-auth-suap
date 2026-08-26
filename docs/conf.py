# Configuration file for Sphinx documentation of django-suap-auth
import os
import sys

# Ensure package root is in Python path
sys.path.insert(0, os.path.abspath(".."))

import django_docs_theme

project = "django-suap-auth"
copyright = "2026, Kelson C. Medeiros"
author = "Kelson C. Medeiros"
release = "1.4.0"
language = "pt_BR"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "django_docs_theme",
]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "django_docs_theme"
html_theme_path = [django_docs_theme.get_html_theme_path()]

html_theme_options = {
    "project_name": "django-suap-auth",
    "tagline": "Backend de autenticação OAuth2 do Django para SUAP",
    "github_url": "https://github.com/django-by-kelsoncm/django-auth-suap",
    "github_repo": "django-by-kelsoncm/django-auth-suap",
    "github_version": "main",
    "doc_path": "docs/",
    "show_edit_on_github": True,
    "navigation_links": (
        "Início|index.html, Instalação|installation.html, Configuração|configuration.html, "
        "Modelos de Perfil|profile-models.html, Endpoints JWT|jwt-endpoints.html, "
        "Escopos|scopes.html, Mapeamento|attribute-mapping.html, Pipeline|user-info-pipeline.html, "
        "Fetchers|fetchers.html, Mappers|mappers.html, Fluxo de Autenticação|auth-flow.html, "
        "Sandboxes|sandboxes.html, Desenvolvimento|development.html, Release|release.html, "
        "GitHub|https://github.com/django-by-kelsoncm/django-auth-suap"
    ),
}


html_static_path = []

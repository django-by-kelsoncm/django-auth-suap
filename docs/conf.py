# Configuration file for Sphinx documentation of django-suap-auth
import os
import sys

# Ensure package root is in Python path
sys.path.insert(0, os.path.abspath(".."))

import django_docs_theme

project = "django-suap-auth"
copyright = "2026, Kelson C. Medeiros"
author = "Kelson C. Medeiros"
release = "1.2.0"
language = "pt_BR"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "django_docs_theme",
]

templates_path = ["_templates"]
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
    "enable_dark_mode": True,
}

html_static_path = ["_static"]

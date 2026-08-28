# Configuration file for Sphinx documentation of django-suap-auth (English)
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import django_docs_theme

project = "django-suap-auth"
copyright = "2026, Kelson C. Medeiros"
author = "Kelson C. Medeiros"
release = "1.8.0"
language = "en"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "django_docs_theme",
]

templates_path = ["../../_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "django_docs_theme"
html_theme_path = [django_docs_theme.get_html_theme_path()]

html_theme_options = {
    "project_name": "django-suap-auth",
    "tagline": "Django OAuth2 authentication backend for SUAP",
    "github_url": "https://github.com/django-by-kelsoncm/django-auth-suap",
    "github_repo": "django-by-kelsoncm/django-auth-suap",
    "github_version": "main",
    "doc_path": "docs/en/1.7.x/",
    "show_edit_on_github": True,
    "navigation_links": (
        "Home|index.html, Installation|installation.html, Configuration|configuration.html, "
        "Profile Models|profile-models.html, Impersonation|impersonation.html, JWT Endpoints|jwt-endpoints.html, "
        "Scopes|scopes.html, Attribute Mapping|attribute-mapping.html, Pipeline|user-info-pipeline.html, "
        "Fetchers|fetchers.html, Mappers|mappers.html, Auth Flow|auth-flow.html, "
        "Sandboxes|sandboxes.html, Development|development.html, Release|release.html, "
        "GitHub|https://github.com/django-by-kelsoncm/django-auth-suap"
    ),
}

html_static_path = []

# -*- coding: utf-8 -*-
"""Affiche le popup de confirmation après création d'un ticket Jira.

Mutualisé par create_jira_from_markdown et create_jira_issue. Non testable
hors-Sublime (view.show_popup + webbrowser).
"""
import webbrowser

from AlfacoLib.jira_popup import (
    build_browse_url,
    project_from_key,
    build_creation_popup_html,
)


def show_created_popup(view, org, key):
    """Popup : clé (lien cliquable vers le navigateur) + projet."""
    project = project_from_key(key)
    browse_url = build_browse_url(org, key)
    html = build_creation_popup_html(key, project, browse_url)
    view.show_popup(html, max_width=480, on_navigate=webbrowser.open)

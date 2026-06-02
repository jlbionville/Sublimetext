# -*- coding: utf-8 -*-
"""Helpers purs pour le popup de confirmation après création d'un ticket Jira.

Isolé de la commande Sublime (non testable hors-Sublime). Construit l'URL
« browse » navigateur, déduit le projet depuis la clé, et rend le minihtml.
"""


def build_browse_url(org, key):
    """URL navigateur d'un ticket : https://{org}.atlassian.net/browse/{key}."""
    return "https://{0}.atlassian.net/browse/{1}".format(org, key)


def project_from_key(key):
    """Projet déduit de la clé : préfixe avant le dernier '-'.

    'MMPO-123' -> 'MMPO' ; une clé sans '-' est retournée telle quelle.
    """
    if "-" in key:
        return key.rsplit("-", 1)[0]
    return key


def build_creation_popup_html(key, project, browse_url):
    """minihtml du popup : clé en lien cliquable + projet + indice."""
    return (
        '<body id="alfaco-jira-created">'
        '<style>'
        'body {{ font-family: system, sans-serif; padding: 6px 10px; }}'
        '.key a {{ font-size: 1.2rem; font-weight: bold; text-decoration: none; }}'
        '.project {{ color: color(var(--foreground) alpha(0.7)); margin-top: 4px; }}'
        '.hint {{ color: color(var(--foreground) alpha(0.5)); font-size: 0.85rem; margin-top: 6px; }}'
        '</style>'
        '<div class="key"><a href="{url}">{key}</a></div>'
        '<div class="project">Projet {project}</div>'
        '<div class="hint">Cliquer pour ouvrir dans le navigateur</div>'
        '</body>'
    ).format(url=browse_url, key=key, project=project)

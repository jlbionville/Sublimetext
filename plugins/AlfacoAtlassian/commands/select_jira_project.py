# -*- coding: utf-8 -*-
"""GET /project/, popup KEY-Nom, stocke project_key."""
import re
import socket
from urllib.error import URLError

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import list_projects


class SelectJiraProjectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        login, password = cfg.jira_auth()
        if not login or not password:
            _atlassian_plugin.log.error(
                f"jira_login/jira_password vide (login={login!r}, password={'(set)' if password else '(empty)'})"
            )
            sublime.error_message(
                "AlfacoAtlassian : `jira_login` ou `jira_password` manquant.\n\n"
                "Renseigner un email et un token API dans :\n"
                "Preferences → Package Settings → AlfacoAtlassian → Settings – User"
            )
            return

        url = cfg.base_url() + "project/"
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération projets depuis {url}…")

        try:
            self._items = list_projects(
                url,
                auth=(login, password),
                headers=cfg.get("headers", {"Accept": "application/json"}),
                verify=cfg.get("tls_verify", True),
            )
        except RuntimeError as e:
            _atlassian_plugin.log.error(str(e))
            sublime.error_message(f"AlfacoAtlassian : la requête a échoué.\n\n{e}")
            return
        except (URLError, socket.timeout) as e:
            _atlassian_plugin.log.error(f"erreur réseau sur {url} : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : impossible de joindre {url}\n\n"
                f"{e}\n\nVérifier `default_organisation` (sous-domaine atlassian.net) et la connectivité."
            )
            return

        if not self._items:
            _atlassian_plugin.log.warn(f"{url} retourne 0 projet")
            sublime.message_dialog(
                "AlfacoAtlassian : aucun projet retourné par Jira.\n\n"
                "Vérifier les droits du compte sur cette organisation."
            )
            return

        _atlassian_plugin.log.info(f"{len(self._items)} projet(s) reçus")
        sublime.status_message(f"AlfacoAtlassian : {len(self._items)} projet(s)")
        self.view.show_popup_menu(self._items, self._on_done)

    def _on_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection projet annulée")
            return
        match = re.match(r"^\w+", self._items[index])
        if match:
            _atlassian_plugin.config.set("project_key", match.group())
            _atlassian_plugin.log.info(f"project_key sélectionné : {match.group()}")
            sublime.status_message(f"AlfacoAtlassian : project_key = {match.group()}")

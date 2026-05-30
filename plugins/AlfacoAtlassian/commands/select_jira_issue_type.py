# -*- coding: utf-8 -*-
"""GET /project/{key}?expand=issueTypes, popup des types, ouvre un buffer Markdown.

À la sélection, délègue à la commande init_markdown_jira en lui passant le nom
du type choisi (champ `# Type` du template). Le payload de création référence le
type par son nom, donc l'id n'est pas nécessaire ; les noms en doublon sont
dédupliqués par parse_issue_type_names.
"""
import socket
from urllib.error import URLError

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, parse_issue_type_names


class SelectJiraIssueTypeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config

        project_key = cfg.get("project_key", "")
        if not project_key:
            _atlassian_plugin.log.error("project_key vide : select_jira_project requis d'abord")
            sublime.error_message(
                "AlfacoAtlassian : aucun projet courant.\n\n"
                "Lance d'abord « Sélectionner projet Jira » (select_jira_project)."
            )
            return

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

        url = cfg.base_url() + "project/" + project_key + "?expand=issueTypes"
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération types depuis {url}…")

        try:
            response = call_rest(
                url,
                body=None,
                auth=(login, password),
                headers=cfg.get("headers", {"Accept": "application/json"}),
                verb="GET",
                verify=cfg.get("tls_verify", True),
            )
        except (URLError, socket.timeout) as e:
            _atlassian_plugin.log.error(f"erreur réseau sur {url} : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : impossible de joindre {url}\n\n"
                f"{e}\n\nVérifier `default_organisation` et la connectivité."
            )
            return

        _atlassian_plugin.log.info(
            f"GET {url} → {response.status_code} ({len(response.text)} bytes)"
        )

        if response.status_code != 200:
            _atlassian_plugin.log.error(
                f"GET {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : la requête a échoué.\n\n"
                f"HTTP {response.status_code}\n{response.text[:500]}"
            )
            return

        try:
            data = response.json()
        except ValueError as e:
            _atlassian_plugin.log.error(
                f"réponse non-JSON ({len(response.text)} bytes) : {e} | preview={response.text[:200]!r}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : réponse non-JSON.\n\n{response.text[:500]}"
            )
            return

        self._items = parse_issue_type_names(data)
        if not self._items:
            _atlassian_plugin.log.warn(
                f"{url} : 0 type (status=200, preview={response.text[:200]!r})"
            )
            sublime.message_dialog(
                f"AlfacoAtlassian : aucun type d'issue retourné pour {project_key}."
            )
            return

        _atlassian_plugin.log.info(f"{len(self._items)} type(s) prêts pour le popup")
        sublime.status_message(f"AlfacoAtlassian : {len(self._items)} type(s)")
        self.view.show_popup_menu(self._items, self._on_done)

    def _on_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection type annulée")
            return
        type_name = self._items[index]
        _atlassian_plugin.log.info(f"type sélectionné : {type_name}")
        self.view.run_command("init_markdown_jira", {"type": type_name})

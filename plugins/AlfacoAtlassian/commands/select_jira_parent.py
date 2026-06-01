# -*- coding: utf-8 -*-
"""Popup des parents (Epic/Story) du projet courant, remplit `# Parent` du buffer.

select_jira_parent : GET .../search?jql=..., popup `KEY — résumé (Type)`.
À la sélection, délègue à set_markdown_parent (commande d'édition) qui écrit la
clé sous la section `# Parent` du buffer Markdown courant. Le périmètre des types
proposés est configurable via `jira_parent_types` (défaut ["Epic", "Story"]).
"""
import re
import socket
from urllib.error import URLError
from urllib.parse import quote

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, parse_parent_choices


class SelectJiraParentCommand(sublime_plugin.TextCommand):
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

        types = cfg.get("jira_parent_types", ["Epic", "Story"])
        clause = ", ".join('"%s"' % t for t in types)
        jql = 'project = "%s" AND issuetype in (%s) ORDER BY created DESC' % (project_key, clause)
        url = cfg.base_url() + "search?jql=" + quote(jql)
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération parents ({project_key})…")

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

        self._choices = parse_parent_choices(data)
        if not self._choices:
            _atlassian_plugin.log.warn(
                f"{url} : 0 parent (status=200, preview={response.text[:200]!r})"
            )
            sublime.message_dialog(
                f"AlfacoAtlassian : aucune Epic/Story trouvée pour {project_key}."
            )
            return

        labels = [label for _, label in self._choices]
        _atlassian_plugin.log.info(f"{len(labels)} parent(s) prêts pour le popup")
        sublime.status_message(f"AlfacoAtlassian : {len(labels)} parent(s)")
        self.view.show_popup_menu(labels, self._on_done)

    def _on_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection parent annulée")
            return
        key = self._choices[index][0]
        _atlassian_plugin.log.info(f"parent sélectionné : {key}")
        self.view.run_command("set_markdown_parent", {"key": key})


class SetMarkdownParentCommand(sublime_plugin.TextCommand):
    """Écrit `key` sous la section `# Parent` du buffer courant.

    Si `# Parent` existe : remplace la ligne suivante par la clé.
    Sinon : insère un bloc `# Parent\\n<key>` avant `# Description`
    (ou en fin de buffer si `# Description` absent).
    """
    def run(self, edit, key):
        view = self.view
        full = sublime.Region(0, view.size())
        text = view.substr(full)
        lines = text.split("\n")

        parent_idx = None
        description_idx = None
        for i, line in enumerate(lines):
            if re.match(r"^#\s+Parent\s*$", line):
                parent_idx = i
            elif re.match(r"^#\s+Description\s*$", line) and description_idx is None:
                description_idx = i

        if parent_idx is not None:
            # Remplace la ligne valeur (juste après le heading) si elle existe et
            # n'est pas un autre heading ; sinon insère la valeur.
            value_idx = parent_idx + 1
            if value_idx < len(lines) and not lines[value_idx].startswith("#"):
                lines[value_idx] = key
            else:
                lines.insert(value_idx, key)
        elif description_idx is not None:
            lines[description_idx:description_idx] = ["# Parent", key, ""]
        else:
            lines += ["", "# Parent", key]

        view.replace(edit, full, "\n".join(lines))
        _atlassian_plugin.log.info(f"# Parent renseigné : {key}")
        sublime.status_message(f"AlfacoAtlassian : parent = {key}")

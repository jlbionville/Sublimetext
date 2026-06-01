# -*- coding: utf-8 -*-
"""Déplace un ticket existant sous un parent (Epic/Story) via PUT /issue/{KEY}.

Flux : input panel (clé du ticket) → popup des Epics/Stories du projet courant
(réutilise parse_parent_choices + jira_parent_types) → PUT du champ `parent`.
Un PUT réussi renvoie 204 No Content (corps vide) : on ne parse pas de JSON.
"""
import json as _json
import socket
from urllib.error import URLError
from urllib.parse import quote

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, parse_parent_choices


class ReparentJiraIssueCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config

        self._project_key = cfg.get("project_key", "")
        if not self._project_key:
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

        window = self.view.window()
        window.show_input_panel(
            "Clé du ticket à déplacer :", "", self._on_issue_key, None, None
        )

    def _on_issue_key(self, issue_key):
        issue_key = issue_key.strip()
        if not issue_key:
            _atlassian_plugin.log.info("re-parentage annulé (clé vide)")
            return
        self._issue_key = issue_key

        cfg = _atlassian_plugin.config
        login, password = cfg.jira_auth()
        types = cfg.get("jira_parent_types", ["Epic", "Story"])
        clause = ", ".join('"%s"' % t for t in types)
        jql = 'project = "%s" AND issuetype in (%s) ORDER BY created DESC' % (self._project_key, clause)
        url = cfg.base_url() + "search?jql=" + quote(jql)
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération parents ({self._project_key})…")

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
                f"AlfacoAtlassian : aucune Epic/Story trouvée pour {self._project_key}."
            )
            return

        labels = [label for _, label in self._choices]
        _atlassian_plugin.log.info(f"{len(labels)} parent(s) prêts pour le popup")
        sublime.status_message(f"AlfacoAtlassian : {len(labels)} parent(s)")
        self.view.show_popup_menu(labels, self._on_parent_done)

    def _on_parent_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection parent annulée")
            return
        parent_key = self._choices[index][0]
        cfg = _atlassian_plugin.config
        payload = _json.dumps(
            {"fields": {"parent": {"key": parent_key}}}, ensure_ascii=False
        )
        url = cfg.base_url() + "issue/" + self._issue_key
        headers = cfg.get(
            "headers", {"Content-type": "application/json", "Accept": "application/json"}
        )
        _atlassian_plugin.log.info(f"PUT {url} parent={parent_key}")
        sublime.status_message(f"AlfacoAtlassian : PUT {self._issue_key} → parent {parent_key}…")

        try:
            response = call_rest(
                url,
                body=payload,
                auth=cfg.jira_auth(),
                headers=headers,
                verb="PUT",
                verify=cfg.get("tls_verify", True),
            )
        except (URLError, socket.timeout) as e:
            _atlassian_plugin.log.error(f"erreur réseau sur {url} : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : impossible de joindre {url}\n\n{e}"
            )
            return

        if response.status_code < 400:
            _atlassian_plugin.log.info(
                f"PUT {url} → {response.status_code} : {self._issue_key} rattaché à {parent_key}"
            )
            sublime.status_message(
                f"AlfacoAtlassian : {self._issue_key} rattaché à {parent_key}"
            )
        else:
            _atlassian_plugin.log.error(
                f"PUT {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : le déplacement a échoué.\n\n"
                f"HTTP {response.status_code}\n{response.text[:500]}"
            )

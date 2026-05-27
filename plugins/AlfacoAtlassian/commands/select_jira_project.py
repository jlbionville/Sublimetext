# -*- coding: utf-8 -*-
"""GET /project/, popup KEY-Nom, stocke project_key.

Diagnostic complet : on appelle call_rest directement (au lieu du wrapper
list_projects) pour pouvoir logger le type/format de la réponse quand le
résultat est vide ou inattendu. Supporte aussi le format paginé v3
(`{"values": [...]}`) en plus du tableau plat (`/project/` v2 et v3 legacy).
"""
import re
import socket
from urllib.error import URLError

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest


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

        # Supporte tableau plat (legacy /project/) ou pagination v3 ({"values": [...]}).
        if isinstance(data, list):
            projects = data
        elif isinstance(data, dict) and isinstance(data.get("values"), list):
            projects = data["values"]
            _atlassian_plugin.log.info(
                f"format paginé détecté : {len(projects)} projet(s) sur cette page"
                + (" (autres pages non récupérées)" if not data.get("isLast", True) else "")
            )
        else:
            _atlassian_plugin.log.error(
                f"format inattendu : type={type(data).__name__} "
                f"keys={list(data.keys()) if isinstance(data, dict) else 'N/A'} "
                f"preview={response.text[:200]!r}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : format de réponse inattendu.\n\n"
                f"Type : {type(data).__name__}\n{response.text[:500]}"
            )
            return

        if not projects:
            _atlassian_plugin.log.warn(
                f"{url} : 0 projet (status=200, body={len(response.text)} bytes, "
                f"preview={response.text[:200]!r})"
            )
            sublime.message_dialog(
                "AlfacoAtlassian : aucun projet retourné.\n\n"
                f"HTTP 200, body = {len(response.text)} octets.\n\n"
                "Cause la plus fréquente : le token API utilisé est lié à un "
                "compte différent de celui logué dans le navigateur (les tokens "
                "Atlassian sont rattachés à un compte spécifique).\n\n"
                f"Compte utilisé ici : {login}\n\n"
                "Vérifie que ce compte voit bien les projets dans le navigateur "
                "(se logger en navigation privée avec cet email)."
            )
            return

        try:
            self._items = [f"{p['key']}-{p['name']}" for p in projects]
        except (KeyError, TypeError) as e:
            _atlassian_plugin.log.error(
                f"items sans key/name : {e} | sample={projects[0] if projects else None}"
            )
            sublime.error_message(
                "AlfacoAtlassian : éléments sans `key` ou `name`.\n\n"
                f"Exemple : {projects[0] if projects else 'N/A'}"
            )
            return

        _atlassian_plugin.log.info(f"{len(self._items)} projet(s) prêts pour le popup")
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

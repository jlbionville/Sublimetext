# -*- coding: utf-8 -*-
"""POST le buffer JSON vers Jira, sauvegarde la réponse et le payload.

Migration de AppelRestApiCommand avec les corrections suivantes :
- Plus de "\\\\" : usage de pathlib.Path (build_response_path / build_payload_path).
- verify TLS et timeout configurables (via Configuration).
- Headers conservés (plus écrasés en cours de route).
- Erreurs HTTP remontées sans masquage.
"""
import time

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest
from AlfacoLib.io import save_file, build_response_path, build_payload_path


class CreateJiraIssueCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        contenu = self.view.substr(sublime.Region(0, self.view.size()))

        url = cfg.base_url() + "issue/"
        headers = cfg.get("headers", {"Content-type": "application/json", "Accept": "application/json"})
        _atlassian_plugin.log.info(f"POST {url} ({len(contenu)} bytes)")
        sublime.status_message(f"AlfacoAtlassian : POST {url}…")

        response = call_rest(
            url,
            body=contenu,
            auth=cfg.jira_auth(),
            headers=headers,
            verb="POST",
            verify=cfg.get("tls_verify", True),
        )

        _atlassian_plugin.log.info(f"POST {url} → {response.status_code}")
        if response.status_code >= 400:
            _atlassian_plugin.log.error(f"POST {url} → {response.status_code} : {response.text[:300]}")
            sublime.status_message(f"AlfacoAtlassian : POST {url} → {response.status_code} (voir buffer réponse)")

        new_view = self.view.window().new_file()
        new_view.set_name(f"Jira response {response.status_code}")
        new_view.run_command("insert", {"characters": response.text})

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            try:
                jira_key = response.json()["key"]
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})")
                sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
            except (KeyError, ValueError):
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (probablement échec — code {response.status_code}) "
                    "— payload non sauvegardé."
                )

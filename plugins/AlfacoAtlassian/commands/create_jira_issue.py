# -*- coding: utf-8 -*-
"""POST le buffer JSON vers Jira, sauvegarde la réponse et le payload.

Migration de AppelRestApiCommand avec les corrections suivantes :
- Plus de "\\\\" : usage de pathlib.Path (build_response_path / build_payload_path).
- verify TLS et timeout configurables (via Configuration).
- Headers conservés (plus écrasés en cours de route).
- Erreurs HTTP remontées sans masquage.
"""
import json as _json
import time

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, wrap_description_as_adf
from AlfacoLib.io import save_file, build_response_path, build_payload_path
from AlfacoAtlassian.commands._created_popup import show_created_popup


class CreateJiraIssueCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        contenu = self.view.substr(sublime.Region(0, self.view.size()))

        # L'API Jira v3 exige description au format ADF. On enveloppe
        # automatiquement les descriptions plain-string pour que le snippet
        # reste lisible côté utilisateur. v2 accepte string telle quelle.
        if cfg.get("api_rest_version", "2") == "3":
            try:
                payload = _json.loads(contenu)
            except ValueError as e:
                _atlassian_plugin.log.error(f"buffer non-JSON, POST avorté : {e}")
                sublime.error_message(
                    f"AlfacoAtlassian : le buffer n'est pas du JSON valide.\n\n{e}"
                )
                return
            wrap_description_as_adf(payload)
            contenu = _json.dumps(payload, ensure_ascii=False, indent=4)
            _atlassian_plugin.log.info(
                "API v3 : description plain-string convertie en ADF avant POST"
            )

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

        # Extraction de la clé (succès = HTTP < 400 ET clé présente).
        jira_key = None
        if response.status_code < 400:
            try:
                jira_key = response.json()["key"]
            except (KeyError, ValueError):
                jira_key = None

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            if jira_key:
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})")
            else:
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (probablement échec — code {response.status_code}) "
                    "— payload non sauvegardé."
                )

        if jira_key:
            org = cfg.get("default_organisation")
            show_created_popup(self.view, org, jira_key)
            sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
        else:
            # Échec : on conserve l'onglet JSON pour diagnostic.
            new_view = self.view.window().new_file()
            new_view.set_name(f"Jira response {response.status_code}")
            new_view.run_command("insert", {"characters": response.text})

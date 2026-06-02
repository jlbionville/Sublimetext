# -*- coding: utf-8 -*-
"""Lit un buffer Markdown, le parse via parse_markdown_jira_template, et POST.

Symétrique à create_jira_issue mais source = Markdown. La conversion
description→ADF est faite par le parser, pas par wrap_description_as_adf.
"""
import json as _json
import time
from datetime import datetime, timedelta

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest
from AlfacoLib.io import save_file, build_response_path, build_payload_path
from AlfacoLib.markdown_to_adf import parse_markdown_jira_template
from AlfacoAtlassian.commands._created_popup import show_created_popup


class CreateJiraFromMarkdownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        text = self.view.substr(sublime.Region(0, self.view.size()))

        today = datetime.now()
        defaults = {
            "project_key": cfg.get("project_key", ""),
            "duedate": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "type": "Task",
            "priority": "High",
            "labels": ["important", "urgent"],
            "startdate_field": cfg.get("jira_startdate_field", "customfield_10015"),
        }

        try:
            payload, meta = parse_markdown_jira_template(text, defaults)
        except ValueError as e:
            _atlassian_plugin.log.error(f"parse_markdown_jira_template : {e}")
            sublime.error_message(f"AlfacoAtlassian (Markdown) : {e}")
            return

        contenu = _json.dumps(payload, ensure_ascii=False, indent=4)
        url = cfg.base_url(org=meta["organisation"] or None) + "issue/"
        headers = cfg.get("headers", {"Content-type": "application/json", "Accept": "application/json"})
        _atlassian_plugin.log.info(f"POST {url} ({len(contenu)} bytes) [from Markdown]")
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
            _atlassian_plugin.log.error(
                f"POST {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.status_message(
                f"AlfacoAtlassian : POST {url} → {response.status_code} (voir buffer réponse)"
            )

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
                _atlassian_plugin.log.info(
                    f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})"
                )
            else:
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (code {response.status_code}) — payload non sauvegardé."
                )

        if jira_key:
            org = meta["organisation"] or cfg.get("default_organisation")
            show_created_popup(self.view, org, jira_key)
            sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
        else:
            # Échec : on conserve l'onglet JSON pour diagnostic.
            new_view = self.view.window().new_file()
            new_view.set_name(f"Jira response {response.status_code}")
            new_view.run_command("insert", {"characters": response.text})

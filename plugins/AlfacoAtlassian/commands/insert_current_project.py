# -*- coding: utf-8 -*-
"""Insère le project_key courant au curseur (ou remplace la sélection)."""
import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class InsertCurrentProjectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        value = _atlassian_plugin.config.get("project_key", "")
        if not value:
            sublime.status_message(
                "AlfacoAtlassian : aucun projet courant (Sélectionner projet Jira)"
            )
            return
        for region in self.view.sel():
            self.view.replace(edit, region, value)

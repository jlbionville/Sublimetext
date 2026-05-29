# -*- coding: utf-8 -*-
"""Insère l'organisation courante (default_organisation) au curseur."""
import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class InsertCurrentOrganisationCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        value = _atlassian_plugin.config.get("default_organisation", "")
        if not value:
            sublime.status_message(
                "AlfacoAtlassian : aucune organisation courante (Sélectionner organisation)"
            )
            return
        for region in self.view.sel():
            self.view.replace(edit, region, value)

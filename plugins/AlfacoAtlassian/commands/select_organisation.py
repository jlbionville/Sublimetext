# -*- coding: utf-8 -*-
"""Affiche les organisations Atlassian configurées et stocke le choix dans la config runtime."""
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class SelectOrganisationCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        atlassian = _atlassian_plugin.config.get("atlassian", {})
        orgs = atlassian.get("organisations", {})
        self._labels = list(orgs.keys())
        self._orgs = orgs
        self.view.show_popup_menu(self._labels, self._on_done)

    def _on_done(self, index):
        if index == -1:
            return
        url_key = self._orgs[self._labels[index]]["url_key"]
        _atlassian_plugin.config.set("default_organisation", url_key)
        _atlassian_plugin.log.info(f"organisation sélectionnée : {url_key}")

# -*- coding: utf-8 -*-
"""Affiche les organisations Atlassian configurées et stocke le choix dans la config runtime."""
import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class SelectOrganisationCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        atlassian = _atlassian_plugin.config.get("atlassian", {})
        orgs = atlassian.get("organisations", {})
        if not orgs:
            _atlassian_plugin.log.error("`atlassian.organisations` vide ou absent des settings")
            sublime.error_message(
                "AlfacoAtlassian : aucune organisation déclarée.\n\n"
                "Renseigne la section `atlassian.organisations` dans :\n"
                "Preferences → Package Settings → AlfacoAtlassian → Settings – User"
            )
            return
        self._labels = list(orgs.keys())
        self._orgs = orgs
        _atlassian_plugin.log.info(f"{len(self._labels)} organisation(s) disponible(s) : {self._labels}")
        self.view.show_popup_menu(self._labels, self._on_done)

    def _on_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection organisation annulée")
            return
        label = self._labels[index]
        try:
            url_key = self._orgs[label]["url_key"]
        except (KeyError, TypeError) as e:
            _atlassian_plugin.log.error(f"organisation `{label}` mal formée : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : entrée `{label}` invalide.\n\n"
                "Chaque organisation doit être un objet avec une clé `url_key`."
            )
            return
        _atlassian_plugin.config.set("default_organisation", url_key)
        _atlassian_plugin.log.info(
            f"organisation sélectionnée : {label} → https://{url_key}.atlassian.net/"
        )
        sublime.status_message(f"AlfacoAtlassian : organisation = {url_key}")

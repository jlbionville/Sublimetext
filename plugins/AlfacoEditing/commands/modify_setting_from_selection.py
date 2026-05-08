# -*- coding: utf-8 -*-
"""Stocke la sélection comme alfaco_delimiter et l'insère à la position du curseur."""
import sublime
import sublime_plugin


class ModifySettingFromSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selected_text = self.view.substr(self.view.sel()[0])
        settings = sublime.load_settings("alfaco-editing.sublime-settings")
        settings.set("alfaco_delimiter", selected_text)
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), settings.get("alfaco_delimiter"))

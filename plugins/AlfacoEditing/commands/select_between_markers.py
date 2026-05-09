# -*- coding: utf-8 -*-
"""Sélectionne le texte entre <start> et <end>, l'ajoute en fin de fichier."""
import sublime
import sublime_plugin


class SelectBetweenMarkersCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        start = self.view.find("<start>", 0)
        end = self.view.find("<end>", 0)
        region = sublime.Region(start.end(), end.begin())
        self.view.sel().clear()
        self.view.sel().add(region)
        selected_text = self.view.substr(region)
        self.view.insert(edit, self.view.size(), "\n" + selected_text)

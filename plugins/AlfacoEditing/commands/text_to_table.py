# -*- coding: utf-8 -*-
"""Commande text_to_table : duplique la sélection (lignes non-vides) en fin de fichier."""
import sublime_plugin


class TextToTableCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selection = self.view.sel()[0]
        selected_text = self.view.substr(selection)
        lines = [line for line in selected_text.split("\n") if line.strip()]
        self.view.insert(edit, self.view.size(), "\n" + "\n".join(lines))

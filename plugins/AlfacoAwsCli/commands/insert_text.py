# -*- coding: utf-8 -*-
"""Commande : insérer du texte brut à chaque curseur (mode guidé)."""
from typing import List

import sublime
import sublime_plugin


class AlfacoAwsCliInsertTextCommand(sublime_plugin.TextCommand):
    """Insère du texte brut à chaque curseur (utilisée par le mode guidé)."""

    def run(self, edit: sublime.Edit, text: str) -> None:
        for region in reversed(list(self.view.sel())):
            if not region.empty():
                self.view.erase(edit, region)
            self.view.insert(edit, region.begin(), text)

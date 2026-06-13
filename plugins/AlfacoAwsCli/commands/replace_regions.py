# -*- coding: utf-8 -*-
"""Commande : remplacer chaque région de sélection par son texte (mode batch)."""
from typing import List

import sublime
import sublime_plugin


class AlfacoAwsCliReplaceRegionsCommand(sublime_plugin.TextCommand):
    """Remplace chaque région de sélection par son texte (mode batch).

    ``texts[i]`` remplace la i-ème région non vide. Le remplacement se
    fait de la fin vers le début pour ne pas invalider les offsets.
    """

    def run(self, edit: sublime.Edit, texts: List[str]) -> None:
        regions = [r for r in self.view.sel() if not r.empty()]
        pairs = list(zip(regions, texts))
        for region, text in reversed(pairs):
            self.view.replace(edit, region, text)

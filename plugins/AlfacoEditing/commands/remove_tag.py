# -*- coding: utf-8 -*-
"""Supprime toutes les occurrences des tags listés (séparés par des virgules)."""
import sublime_plugin


class RemoveTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        tags = text.split(",")
        for tag in tags:
            for region in reversed(self.view.find_all(tag)):
                self.view.erase(edit, region)

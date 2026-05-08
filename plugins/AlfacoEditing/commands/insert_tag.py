# -*- coding: utf-8 -*-
"""Insère un tag arbitraire à la position du curseur."""
import sublime_plugin


class InsertTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        pos = self.view.sel()[0].begin()
        self.view.insert(edit, pos, text)

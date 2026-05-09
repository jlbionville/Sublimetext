# -*- coding: utf-8 -*-
"""Affiche le chemin du fichier ouvert dans la console."""
import sublime
import sublime_plugin


class ShowFileNameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        active_view = sublime.active_window().active_view()
        file_name = active_view.file_name()
        if file_name:
            print(f"Le fichier ouvert dans la vue actuelle est : {file_name}")
        else:
            print("Aucun fichier ouvert dans la vue actuelle")

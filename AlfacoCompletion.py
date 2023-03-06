# -*- coding: utf-8 -*-

import sublime
import sublime_plugin


class AlfacoCompletion(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.python"):
            return []

        available_completions = [
            "def",
            "class",
            "None",
            "True",
            "False"
        ]

        prefix = prefix.lower()

        out = []
        for comp in available_completions:
            if comp.lower().startswith(prefix):
                out.append(comp)

        return out
# -*- coding: utf-8 -*-
"""Auto-complétion statique pour les buffers Python."""
import sublime_plugin


class AlfacoCompletion(sublime_plugin.EventListener):
    AVAILABLE = ["def", "class", "None", "True", "False"]

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.python"):
            return []
        prefix = prefix.lower()
        return [c for c in self.AVAILABLE if c.lower().startswith(prefix)]

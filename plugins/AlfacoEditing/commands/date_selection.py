# -*- coding: utf-8 -*-
"""Calcule date+N (N lu dans la sélection), ouvre un nouveau buffer avec le résultat."""
from datetime import datetime, timedelta

import sublime_plugin


class DateSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        num_days = int(self.view.substr(self.view.sel()[0]))
        future = (datetime.now() + timedelta(days=num_days)).strftime("%Y-%m-%d")
        output = f"##dt: {future} "
        new_view = self.view.window().new_file()
        new_view.run_command("insert", {"characters": output})

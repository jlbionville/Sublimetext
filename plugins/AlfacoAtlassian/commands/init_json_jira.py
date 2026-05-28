# -*- coding: utf-8 -*-
"""Ouvre un buffer scratch et y insère le snippet jira pré-rempli."""
from datetime import datetime, timedelta

import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class InitJsonJiraCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        current_line = self.view.substr(self.view.line(self.view.sel()[0]))
        new_view = self.view.window().new_file()
        new_view.set_name("Init new Jira")
        new_view.set_scratch(True)
        today = datetime.now()
        args["duedate"] = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        args["selection"] = current_line.strip()
        args["jira_key"] = _atlassian_plugin.config.get("project_key", "")
        new_view.run_command("insert_snippet", args)

# -*- coding: utf-8 -*-
"""Ouvre un buffer Markdown scratch avec le template Jira pré-rempli."""
from datetime import datetime, timedelta

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class InitMarkdownJiraCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        new_view = self.view.window().new_file()
        new_view.set_name("Init new Jira (Markdown)")
        new_view.set_scratch(True)
        new_view.assign_syntax("Packages/Markdown/Markdown.sublime-syntax")

        today = datetime.now()
        args.setdefault(
            "name",
            "Packages/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet",
        )
        args["organisation"] = _atlassian_plugin.config.get("default_organisation", "")
        args["startdate"] = today.strftime("%Y-%m-%d")
        args["duedate"] = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        args["jira_key"] = _atlassian_plugin.config.get("project_key", "")
        args.setdefault("type", "Task")
        args.setdefault("parent", "")

        _atlassian_plugin.log.info(
            f"init_markdown_jira : template inséré (project_key={args['jira_key']!r})"
        )
        sublime.status_message("AlfacoAtlassian : template Markdown inséré")
        new_view.run_command("insert_snippet", args)

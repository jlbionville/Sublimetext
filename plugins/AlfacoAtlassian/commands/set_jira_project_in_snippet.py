# -*- coding: utf-8 -*-
"""Remplace "key": "" par "key": "<args.text>" dans le buffer."""
import re

import sublime
import sublime_plugin


class SetJiraProjectInSnippetCommand(sublime_plugin.TextCommand):
    def run(self, edit, args):
        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)
        pattern = r'"key"\s*:\s*(""|\'\')'
        content = re.sub(pattern, f'"key": "{args["text"]}"', content)
        self.view.replace(edit, region, content)

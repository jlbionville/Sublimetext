# -*- coding: utf-8 -*-
"""GET /project/, popup KEY-Nom, stocke project_key."""
import re

import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import list_projects


class SelectJiraProjectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        try:
            self._items = list_projects(
                cfg.base_url() + "project/",
                auth=cfg.jira_auth(),
                headers=cfg.get("headers", {"Accept": "application/json"}),
                verify=cfg.get("tls_verify", True),
            )
        except RuntimeError as e:
            _atlassian_plugin.log.warn(str(e))
            return
        self.view.show_popup_menu(self._items, self._on_done)

    def _on_done(self, index):
        if index == -1:
            return
        match = re.match(r"^\w+", self._items[index])
        if match:
            _atlassian_plugin.config.set("project_key", match.group())
            _atlassian_plugin.log.info(f"project_key : {match.group()}")

# -*- coding: utf-8 -*-
"""Affiche le login Jira en console (sans le password — bug du legacy corrigé)."""
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class OpenJiraProjectsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        login, _password = _atlassian_plugin.config.jira_auth()
        _atlassian_plugin.log.info(f"jira_login = {login}")
        _atlassian_plugin.log.info("jira_password : (masqué)")

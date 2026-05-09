# -*- coding: utf-8 -*-
"""Configuration partagée entre plugins Alfaco.

Empile plusieurs fichiers .sublime-settings + un dictionnaire runtime.
Aucun effet de bord sur Preferences.sublime-settings (contrairement au code legacy).
"""
from __future__ import annotations

import sublime


class Configuration:
    """Configuration empilée pour un plugin Alfaco."""

    def __init__(self, settings_files):
        self._settings_files = list(settings_files)
        self._loaded = None
        self._runtime = {}

    def _ensure_loaded(self):
        if self._loaded is None:
            self._loaded = [sublime.load_settings(name) for name in self._settings_files]
        return self._loaded

    def get(self, key, default=None):
        if key in self._runtime:
            return self._runtime[key]
        for layer in self._ensure_loaded():
            if layer.has(key):
                return layer.get(key)
        return default

    def set(self, key, value):
        self._runtime[key] = value

    def jira_auth(self):
        return (self.get("jira_login"), self.get("jira_password"))

    def base_url(self, version=None):
        org = self.get("default_organisation")
        ver = version if version is not None else self.get("api_rest_version", "2")
        return f"https://{org}.atlassian.net/rest/api/{ver}/"

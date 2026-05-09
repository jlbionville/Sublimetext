# -*- coding: utf-8 -*-
"""Helpers IO sans dépendances Sublime.

Substitut moderne de modules/tools.py (saveFichier/readFichier) :
- encodage UTF-8 explicite
- création des dossiers parents
- chemins via pathlib (cross-platform, plus de '\\' codés en dur)
"""
from __future__ import annotations

from pathlib import Path


def save_file(content, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def read_file(path):
    return Path(path).read_text(encoding="utf-8")


def build_response_path(folder, timestamp):
    return Path(folder) / f"error_api_call_{timestamp}.html"


def build_payload_path(folder, jira_key):
    return Path(folder) / f"{jira_key}.json"

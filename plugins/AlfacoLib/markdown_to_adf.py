# -*- coding: utf-8 -*-
"""Parser de template Markdown Jira et convertisseur Markdown → ADF.

Module pur (pas d'import sublime), testable hors-Sublime. Voir la spec
docs/superpowers/specs/2026-05-27-markdown-to-jira-design.md pour le contrat.
"""
from __future__ import annotations


def _parse_inline(text):
    """Convertit une string Markdown inline (sans newlines) en liste de
    text nodes ADF, avec marks appliquées (strong, em, code, link).
    """
    if not text:
        return []
    return [{"type": "text", "text": text}]

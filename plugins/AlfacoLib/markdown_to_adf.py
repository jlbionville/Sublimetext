# -*- coding: utf-8 -*-
"""Parser de template Markdown Jira et convertisseur Markdown → ADF.

Module pur (pas d'import sublime), testable hors-Sublime. Voir la spec
docs/superpowers/specs/2026-05-27-markdown-to-jira-design.md pour le contrat.
"""
from __future__ import annotations

import re

# Ordre = priorité. Le premier qui matche emporte la portion de texte.
_INLINE_PATTERNS = [
    # ⚠ strong AVANT em (sinon ** est matché comme deux *) ; le moteur préfère
    # le match le plus précoce, mais à position égale on garde l'ordre déclaré.
    ("strong", re.compile(r"\*\*(.+?)\*\*|__(.+?)__")),
    ("em", re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)|(?<!_)_([^_]+?)_(?!_)")),
    ("code", re.compile(r"`([^`]+)`")),
    ("link", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
]


def _build_mark(mark_type, match):
    if mark_type == "link":
        return [{"type": "link", "attrs": {"href": match.group(2)}}]
    return [{"type": mark_type}]


def _parse_inline(text):
    """Convertit une string Markdown inline en liste de text nodes ADF."""
    if not text:
        return []
    nodes = []
    cursor = 0
    while cursor < len(text):
        best = None
        for mark_type, pattern in _INLINE_PATTERNS:
            match = pattern.search(text, cursor)
            if match and (best is None or match.start() < best[1].start()):
                best = (mark_type, match)
        if best is None:
            nodes.append({"type": "text", "text": text[cursor:]})
            break
        mark_type, match = best
        if match.start() > cursor:
            nodes.append({"type": "text", "text": text[cursor:match.start()]})
        inner = next(g for g in match.groups() if g is not None)
        nodes.append({
            "type": "text",
            "text": inner,
            "marks": _build_mark(mark_type, match),
        })
        cursor = match.end()
    return nodes

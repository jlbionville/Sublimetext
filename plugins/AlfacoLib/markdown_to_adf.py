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


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_BULLET_RE = re.compile(r"^[-*+]\s+(.+)$")
_ORDERED_RE = re.compile(r"^\d+\.\s+(.+)$")


def _parse_list(lines, item_re, list_type):
    items = []
    for line in lines:
        m = item_re.match(line)
        if not m:
            continue
        items.append({
            "type": "listItem",
            "content": [
                {"type": "paragraph", "content": _parse_inline(m.group(1))}
            ],
        })
    return {"type": list_type, "content": items}


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


def _split_blocks(md_text):
    """Découpe en blocs : un bloc = lignes contigües séparées par une ligne vide.
    Retourne list[list[str]] (chaque sous-liste = lignes du bloc, sans newlines).
    """
    blocks = []
    current = []
    for line in md_text.split("\n"):
        if line.strip():
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def _parse_block(lines):
    """Convertit un bloc (liste de lignes) en un node ADF top-level."""
    first = lines[0]
    if _BULLET_RE.match(first):
        return _parse_list(lines, _BULLET_RE, "bulletList")
    if _ORDERED_RE.match(first):
        return _parse_list(lines, _ORDERED_RE, "orderedList")
    m = _HEADING_RE.match(first)
    if m:
        level = len(m.group(1))
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": _parse_inline(m.group(2)),
        }
    # Paragraphe : soft-join sur espace
    text = " ".join(lines)
    return {"type": "paragraph", "content": _parse_inline(text)}


def _markdown_to_adf(md_text):
    """Convertit du Markdown en document ADF top-level."""
    blocks = _split_blocks(md_text)
    content = [_parse_block(b) for b in blocks]
    if not content:
        content = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": content}

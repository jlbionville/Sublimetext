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
_FENCE_RE = re.compile(r"^```(\w*)$")


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
    """Découpe en blocs. Un code-block fence (```…```) est préservé entier
    même s'il contient des lignes vides."""
    blocks = []
    current = []
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _FENCE_RE.match(line)
        if m:
            if current:
                blocks.append(current)
                current = []
            fence_lines = [line]
            i += 1
            while i < len(lines) and lines[i] != "```":
                fence_lines.append(lines[i])
                i += 1
            if i < len(lines):
                fence_lines.append(lines[i])  # closing ```
            blocks.append(fence_lines)
            i += 1
            continue
        if line.strip():
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
        i += 1
    if current:
        blocks.append(current)
    return blocks


def _parse_block(lines):
    """Convertit un bloc (liste de lignes) en un node ADF top-level."""
    first = lines[0]
    m_fence = _FENCE_RE.match(first)
    if m_fence:
        language = m_fence.group(1)
        body_lines = lines[1:]
        if body_lines and body_lines[-1] == "```":
            body_lines = body_lines[:-1]
        code = "\n".join(body_lines)
        node = {"type": "codeBlock", "content": [{"type": "text", "text": code}]}
        if language:
            node["attrs"] = {"language": language}
        return node
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


KNOWN_FIELDS = [
    "Summary", "Project", "Type", "Priority", "Labels",
    "Startdate", "Duedate", "Description",
]


def _split_fields(text):
    """Découpe un template Markdown sur les headings H1 et retourne
    {field_name: body}. La section `# Description` capture jusqu'à EOF.

    Raises:
        ValueError si un champ inconnu (non dans KNOWN_FIELDS) est rencontré
        avant `# Description`.
    """
    fields = {}
    current_field = None
    current_lines = []
    in_description = False
    for line in text.split("\n"):
        if not in_description:
            m = re.match(r"^#\s+(\w+)\s*$", line)
            if m:
                field_name = m.group(1)
                if current_field is not None:
                    fields[current_field] = "\n".join(current_lines).strip()
                if field_name not in KNOWN_FIELDS:
                    raise ValueError(
                        f"Champ inconnu '# {field_name}'. "
                        f"Champs reconnus : {', '.join(KNOWN_FIELDS)}."
                    )
                current_field = field_name
                current_lines = []
                if field_name == "Description":
                    in_description = True
                continue
        if current_field is not None:
            current_lines.append(line)
    if current_field is not None:
        body = "\n".join(current_lines)
        if current_field == "Description":
            fields[current_field] = body.strip("\n")
        else:
            fields[current_field] = body.strip()
    return fields

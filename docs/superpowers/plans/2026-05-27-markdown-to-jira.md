# Markdown → Jira Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre la création de tickets Jira depuis un buffer Markdown (template à headings H1 + corps Markdown converti en ADF), parallèlement au flux JSON existant.

**Architecture:** Module pur `AlfacoLib/markdown_to_adf.py` (parser regex stdlib, testable hors-Sublime) consommé par deux nouvelles commandes `InitMarkdownJiraCommand` (insertion template) et `CreateJiraFromMarkdownCommand` (parse + POST). Snippet `.sublime-snippet-markdown` pour le template, 2 raccourcis × 3 OS, entrées menu.

**Tech Stack:** Python 3.8+ stdlib uniquement (`re`, `json`), pytest hors-Sublime, Sublime Text plugin API.

**Spec:** [`docs/superpowers/specs/2026-05-27-markdown-to-jira-design.md`](../specs/2026-05-27-markdown-to-jira-design.md)

---

### Task 1: Branche + scaffold des nouveaux fichiers

**Files:**
- Create: `plugins/AlfacoLib/markdown_to_adf.py` (vide initialement, sera complété aux tâches 2-9)
- Create: `plugins/AlfacoLib/tests/test_markdown_to_adf.py` (vide)

- [ ] **Step 1: Créer la branche depuis main à jour**

```bash
git checkout main
git pull
git checkout -b feat/markdown-to-jira
```

- [ ] **Step 2: Créer le module vide**

Contenu de `plugins/AlfacoLib/markdown_to_adf.py` :

```python
# -*- coding: utf-8 -*-
"""Parser de template Markdown Jira et convertisseur Markdown → ADF.

Module pur (pas d'import sublime), testable hors-Sublime. Voir la spec
docs/superpowers/specs/2026-05-27-markdown-to-jira-design.md pour le contrat.
"""
from __future__ import annotations
```

- [ ] **Step 3: Créer le fichier de test avec import**

Contenu de `plugins/AlfacoLib/tests/test_markdown_to_adf.py` :

```python
"""Tests du parser Markdown → Jira (ADF)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
```

- [ ] **Step 4: Vérifier que la suite tourne toujours**

Run: `make test`
Expected: 48 passed (les tests existants, le nouveau fichier ne contient pas encore de tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): scaffold module + test file"
```

---

### Task 2: Inline marks — texte plain

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire le test (RED)**

Ajouter dans `test_markdown_to_adf.py` :

```python
from AlfacoLib.markdown_to_adf import _parse_inline  # noqa: E402


def test_parse_inline_plain_text():
    """Texte sans marks → un seul text node sans marks."""
    assert _parse_inline("hello world") == [
        {"type": "text", "text": "hello world"}
    ]


def test_parse_inline_empty_string():
    assert _parse_inline("") == []
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: ImportError (`_parse_inline` n'existe pas).

- [ ] **Step 3: Implémenter minimum**

Ajouter dans `markdown_to_adf.py` :

```python
def _parse_inline(text):
    """Convertit une string Markdown inline (sans newlines) en liste de
    text nodes ADF, avec marks appliquées (strong, em, code, link).
    """
    if not text:
        return []
    return [{"type": "text", "text": text}]
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _parse_inline plain text"
```

---

### Task 3: Inline marks — strong (gras)

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

Ajouter à `test_markdown_to_adf.py` :

```python
def test_parse_inline_bold_double_asterisk():
    assert _parse_inline("**bold**") == [
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]}
    ]


def test_parse_inline_bold_double_underscore():
    assert _parse_inline("__bold__") == [
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]}
    ]


def test_parse_inline_bold_with_surrounding_text():
    assert _parse_inline("voici **important** ici") == [
        {"type": "text", "text": "voici "},
        {"type": "text", "text": "important", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " ici"},
    ]
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 3 nouveaux tests FAIL.

- [ ] **Step 3: Implémenter via regex itérative**

Remplacer `_parse_inline` dans `markdown_to_adf.py` par :

```python
import re

# Ordre = priorité. Le premier qui matche emporte la portion de texte.
_INLINE_PATTERNS = [
    ("strong", re.compile(r"\*\*(.+?)\*\*|__(.+?)__")),
]


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
        nodes.append({"type": "text", "text": inner, "marks": [{"type": mark_type}]})
        cursor = match.end()
    return nodes
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _parse_inline strong (**bold**, __bold__)"
```

---

### Task 4: Inline marks — em (italique)

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
def test_parse_inline_italic_single_asterisk():
    assert _parse_inline("*ital*") == [
        {"type": "text", "text": "ital", "marks": [{"type": "em"}]}
    ]


def test_parse_inline_italic_single_underscore():
    assert _parse_inline("_ital_") == [
        {"type": "text", "text": "ital", "marks": [{"type": "em"}]}
    ]


def test_parse_inline_strong_then_em():
    """**bold** et *italic* → 4 nodes (bold, ' et ', italic) + texte autour."""
    assert _parse_inline("**A** et *B*") == [
        {"type": "text", "text": "A", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " et "},
        {"type": "text", "text": "B", "marks": [{"type": "em"}]},
    ]
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 3 nouveaux tests FAIL.

- [ ] **Step 3: Implémenter**

Mettre à jour `_INLINE_PATTERNS` dans `markdown_to_adf.py` :

```python
_INLINE_PATTERNS = [
    # ⚠ strong AVANT em (sinon ** est matché comme deux *) ; le moteur préfère
    # le match le plus précoce, mais à position égale on garde l'ordre déclaré.
    ("strong", re.compile(r"\*\*(.+?)\*\*|__(.+?)__")),
    ("em", re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)|(?<!_)_([^_]+?)_(?!_)")),
]
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _parse_inline em (*italic*, _italic_)"
```

---

### Task 5: Inline marks — code inline + link

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
def test_parse_inline_code():
    assert _parse_inline("voir `git pull`") == [
        {"type": "text", "text": "voir "},
        {"type": "text", "text": "git pull", "marks": [{"type": "code"}]},
    ]


def test_parse_inline_link():
    assert _parse_inline("[Atlassian](https://x.io)") == [
        {
            "type": "text",
            "text": "Atlassian",
            "marks": [{"type": "link", "attrs": {"href": "https://x.io"}}],
        }
    ]


def test_parse_inline_link_with_surrounding_text():
    assert _parse_inline("voir [doc](http://a) ici") == [
        {"type": "text", "text": "voir "},
        {
            "type": "text",
            "text": "doc",
            "marks": [{"type": "link", "attrs": {"href": "http://a"}}],
        },
        {"type": "text", "text": " ici"},
    ]
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 3 nouveaux tests FAIL.

- [ ] **Step 3: Implémenter — link nécessite gestion attrs**

Refactor `_parse_inline` dans `markdown_to_adf.py` (le mark `link` a un `attrs.href` à extraire) :

```python
_INLINE_PATTERNS = [
    ("strong", re.compile(r"\*\*(.+?)\*\*|__(.+?)__")),
    ("em", re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)|(?<!_)_([^_]+?)_(?!_)")),
    ("code", re.compile(r"`([^`]+)`")),
    ("link", re.compile(r"\[([^\]]+)\]\(([^)]+)\)")),
]


def _build_mark(mark_type, match):
    if mark_type == "link":
        return [{"type": "link", "attrs": {"href": match.group(2)}}]
    return [{"type": mark_type}]


def _extract_inner_text(mark_type, match):
    return match.group(1)


def _parse_inline(text):
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
        inner = _extract_inner_text(mark_type, match)
        if inner is None:  # alternance regex (e.g. __bold__ second group)
            inner = next(g for g in match.groups() if g is not None)
        nodes.append({
            "type": "text",
            "text": inner,
            "marks": _build_mark(mark_type, match),
        })
        cursor = match.end()
    return nodes
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _parse_inline code inline + link"
```

---

### Task 6: Block parser — paragraphes et heading

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
from AlfacoLib.markdown_to_adf import _markdown_to_adf  # noqa: E402


def test_block_single_paragraph():
    assert _markdown_to_adf("hello world") == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "hello world"}],
            }
        ],
    }


def test_block_two_paragraphs_separated_by_blank_line():
    md = "para 1\n\npara 2"
    doc = _markdown_to_adf(md)
    assert len(doc["content"]) == 2
    assert doc["content"][0]["content"][0]["text"] == "para 1"
    assert doc["content"][1]["content"][0]["text"] == "para 2"


def test_block_heading_level_2():
    doc = _markdown_to_adf("## Sub-section")
    assert doc["content"] == [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Sub-section"}],
        }
    ]


def test_block_heading_levels_1_to_6():
    for level in range(1, 7):
        md = "#" * level + " Titre"
        doc = _markdown_to_adf(md)
        assert doc["content"][0]["type"] == "heading"
        assert doc["content"][0]["attrs"]["level"] == level


def test_block_paragraph_joins_soft_lines():
    """Sans ligne vide, deux lignes Markdown = un seul paragraphe (joint par espace)."""
    doc = _markdown_to_adf("ligne 1\nligne 2")
    assert doc["content"] == [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "ligne 1 ligne 2"}],
        }
    ]
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 5 nouveaux tests FAIL (ImportError ou AssertionError).

- [ ] **Step 3: Implémenter le block parser**

Ajouter dans `markdown_to_adf.py` :

```python
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


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
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _markdown_to_adf paragraphes + headings"
```

---

### Task 7: Block parser — bullet list + ordered list

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
def test_block_bullet_list_dash():
    doc = _markdown_to_adf("- item 1\n- item 2")
    assert doc["content"] == [
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "item 1"}
                        ]}
                    ],
                },
                {
                    "type": "listItem",
                    "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "item 2"}
                        ]}
                    ],
                },
            ],
        }
    ]


def test_block_bullet_list_star_or_plus():
    """`*` et `+` sont aussi valides comme bullets."""
    for marker in ("*", "+"):
        doc = _markdown_to_adf(f"{marker} foo\n{marker} bar")
        assert doc["content"][0]["type"] == "bulletList"
        assert len(doc["content"][0]["content"]) == 2


def test_block_ordered_list():
    doc = _markdown_to_adf("1. premier\n2. second")
    assert doc["content"][0]["type"] == "orderedList"
    assert len(doc["content"][0]["content"]) == 2
    assert doc["content"][0]["content"][0]["content"][0]["content"][0]["text"] == "premier"


def test_block_list_items_with_inline_marks():
    """Les items conservent les marks inline."""
    doc = _markdown_to_adf("- **bold** item")
    item_para = doc["content"][0]["content"][0]["content"][0]
    assert item_para["content"] == [
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " item"},
    ]
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 4 nouveaux tests FAIL.

- [ ] **Step 3: Implémenter**

Ajouter dans `markdown_to_adf.py` (avant `_parse_block`) :

```python
_BULLET_RE = re.compile(r"^[-*+]\s+(.+)$")
_ORDERED_RE = re.compile(r"^\d+\.\s+(.+)$")


def _parse_list(lines, item_re, list_type):
    items = []
    for line in lines:
        m = item_re.match(line)
        if not m:
            # ligne qui n'est pas un item de liste = on l'attache au précédent
            # (soft continuation). MVP : on ignore proprement.
            continue
        items.append({
            "type": "listItem",
            "content": [
                {"type": "paragraph", "content": _parse_inline(m.group(1))}
            ],
        })
    return {"type": list_type, "content": items}
```

Modifier `_parse_block` pour détecter les listes :

```python
def _parse_block(lines):
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
    text = " ".join(lines)
    return {"type": "paragraph", "content": _parse_inline(text)}
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 20 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _parse_block bullet/ordered lists"
```

---

### Task 8: Block parser — code block (triple backticks)

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
def test_block_code_block_with_language():
    md = "```python\nprint('hi')\n```"
    doc = _markdown_to_adf(md)
    assert doc["content"] == [
        {
            "type": "codeBlock",
            "attrs": {"language": "python"},
            "content": [{"type": "text", "text": "print('hi')"}],
        }
    ]


def test_block_code_block_without_language():
    md = "```\nfoo\nbar\n```"
    doc = _markdown_to_adf(md)
    assert doc["content"][0]["type"] == "codeBlock"
    assert "attrs" not in doc["content"][0] or doc["content"][0].get("attrs") == {}
    assert doc["content"][0]["content"][0]["text"] == "foo\nbar"


def test_block_code_block_preserves_indentation():
    md = "```\n    indented\n```"
    doc = _markdown_to_adf(md)
    assert doc["content"][0]["content"][0]["text"] == "    indented"
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 3 nouveaux tests FAIL.

- [ ] **Step 3: Implémenter — code block traverse plusieurs blocs**

Le découpage actuel `_split_blocks` casse sur les lignes vides — un code block contenant une ligne vide serait découpé en deux. Il faut un pré-traitement.

Refactor : transformer `_split_blocks` pour reconnaître les fences ` ``` ` et garder leur contenu intact.

Remplacer `_split_blocks` dans `markdown_to_adf.py` :

```python
_FENCE_RE = re.compile(r"^```(\w*)$")


def _split_blocks(md_text):
    """Découpe en blocs. Un code-block fence (```…```) est préservé entier
    même s'il contient des lignes vides."""
    blocks = []
    current = []
    in_fence = False
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not in_fence:
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
```

Ajouter la branche `codeBlock` dans `_parse_block` :

```python
def _parse_block(lines):
    first = lines[0]
    m_fence = _FENCE_RE.match(first)
    if m_fence:
        language = m_fence.group(1)
        # Contenu = lignes entre fence ouvrante et fermante
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
    text = " ".join(lines)
    return {"type": "paragraph", "content": _parse_inline(text)}
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 23 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _parse_block code blocks (triple backticks)"
```

---

### Task 9: Field splitter (H1 sections)

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
from AlfacoLib.markdown_to_adf import _split_fields, KNOWN_FIELDS  # noqa: E402


def test_known_fields_constants():
    """Les 8 champs réservés du template."""
    assert KNOWN_FIELDS == [
        "Summary", "Project", "Type", "Priority", "Labels",
        "Startdate", "Duedate", "Description",
    ]


def test_split_fields_minimal_template():
    template = "# Summary\nfoo\n\n# Description\nbar"
    result = _split_fields(template)
    assert result == {"Summary": "foo", "Description": "bar"}


def test_split_fields_all_fields():
    template = (
        "# Summary\nS\n\n"
        "# Project\nPRJ\n\n"
        "# Type\nTask\n\n"
        "# Priority\nHigh\n\n"
        "# Labels\nimportant, urgent\n\n"
        "# Startdate\n2026-05-27\n\n"
        "# Duedate\n2026-06-06\n\n"
        "# Description\nbody"
    )
    result = _split_fields(template)
    assert set(result.keys()) == set(KNOWN_FIELDS)
    assert result["Labels"] == "important, urgent"


def test_split_fields_description_captures_until_eof():
    """Tout ce qui suit `# Description` est dans Description, y compris h2+."""
    template = (
        "# Summary\nfoo\n\n"
        "# Description\nintro\n\n## Sub-section\n- item\n"
    )
    result = _split_fields(template)
    assert result["Description"] == "intro\n\n## Sub-section\n- item"


def test_split_fields_unknown_field_raises():
    template = "# Summary\nfoo\n\n# Bogus\nx\n\n# Description\nbar"
    try:
        _split_fields(template)
    except ValueError as e:
        assert "Bogus" in str(e)
        assert "Summary" in str(e)  # liste les champs connus
    else:
        assert False, "ValueError attendue"


def test_split_fields_trims_field_body():
    template = "# Summary\n  foo  \n\n# Description\nbar"
    result = _split_fields(template)
    assert result["Summary"] == "foo"
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 6 nouveaux tests FAIL (ImportError).

- [ ] **Step 3: Implémenter**

Ajouter dans `markdown_to_adf.py` :

```python
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
                # flush previous
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
        # Trim leading/trailing blank lines mais préserve les newlines internes
        # (important pour Description qui peut contenir du Markdown multi-paragraphe).
        if current_field == "Description":
            fields[current_field] = body.strip("\n")
        else:
            fields[current_field] = body.strip()
    return fields
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 29 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): _split_fields (H1 sections, Description→EOF)"
```

---

### Task 10: parse_markdown_jira_template — fonction publique + validation

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`

- [ ] **Step 1: Écrire les tests (RED)**

```python
from AlfacoLib.markdown_to_adf import parse_markdown_jira_template  # noqa: E402


_DEFAULTS = {
    "project_key": "SDAL",
    "startdate": "2026-05-27",
    "duedate": "2026-06-06",
    "type": "Task",
    "priority": "High",
    "labels": ["important", "urgent"],
}


def test_parse_full_template_returns_payload_with_adf():
    template = (
        "# Summary\nDevelopper feature\n\n"
        "# Description\nLe contexte.\n\n- item 1\n- item 2"
    )
    payload = parse_markdown_jira_template(template, _DEFAULTS)
    fields = payload["fields"]
    assert fields["summary"] == "Developper feature"
    assert fields["project"] == {"key": "SDAL"}
    assert fields["issuetype"] == {"name": "Task", "subtask": False}
    assert fields["priority"] == {"name": "High"}
    assert fields["labels"] == ["important", "urgent"]
    assert fields["startdate"] == "2026-05-27"
    assert fields["duedate"] == "2026-06-06"
    # description = ADF doc avec 2 blocs (paragraphe + bulletList)
    assert fields["description"]["type"] == "doc"
    assert len(fields["description"]["content"]) == 2


def test_parse_template_overrides_defaults():
    template = (
        "# Summary\nS\n# Project\nFOO\n# Type\nBug\n# Priority\nLow\n"
        "# Labels\na, b\n# Startdate\n2026-01-01\n# Duedate\n2026-01-10\n"
        "# Description\nbody"
    )
    payload = parse_markdown_jira_template(template, _DEFAULTS)
    fields = payload["fields"]
    assert fields["project"] == {"key": "FOO"}
    assert fields["issuetype"] == {"name": "Bug", "subtask": False}
    assert fields["priority"] == {"name": "Low"}
    assert fields["labels"] == ["a", "b"]
    assert fields["startdate"] == "2026-01-01"
    assert fields["duedate"] == "2026-01-10"


def test_parse_template_summary_required():
    template = "# Description\nbar"
    try:
        parse_markdown_jira_template(template, _DEFAULTS)
    except ValueError as e:
        assert "Summary" in str(e)
    else:
        assert False, "ValueError attendue"


def test_parse_template_description_required():
    template = "# Summary\nfoo"
    try:
        parse_markdown_jira_template(template, _DEFAULTS)
    except ValueError as e:
        assert "Description" in str(e)
    else:
        assert False, "ValueError attendue"


def test_parse_template_project_required_without_default():
    template = "# Summary\nS\n\n# Description\nbody"
    no_project = dict(_DEFAULTS)
    no_project["project_key"] = ""
    try:
        parse_markdown_jira_template(template, no_project)
    except ValueError as e:
        assert "Project" in str(e) or "project_key" in str(e)
    else:
        assert False, "ValueError attendue"


def test_parse_template_labels_csv_split():
    template = (
        "# Summary\nS\n\n# Labels\nfoo,  bar ,baz  \n\n"
        "# Description\nbody"
    )
    payload = parse_markdown_jira_template(template, _DEFAULTS)
    assert payload["fields"]["labels"] == ["foo", "bar", "baz"]
```

- [ ] **Step 2: Vérifier RED**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: les 6 nouveaux tests FAIL.

- [ ] **Step 3: Implémenter la fonction publique**

Ajouter à la fin de `markdown_to_adf.py` :

```python
def parse_markdown_jira_template(text, defaults):
    """Parse un template Markdown Jira en payload `{fields: {...}}` complet.

    Args:
        text: contenu Markdown du template (cf. spec pour le format).
        defaults: dict avec `project_key`, `startdate`, `duedate`, `type`,
            `priority`, `labels` utilisés comme fallback si le champ
            correspondant est absent du template.

    Returns:
        dict `{"fields": {...}}` prêt à JSON-dump et POST sur l'API Jira v3
        (description en ADF).

    Raises:
        ValueError: champ obligatoire absent, champ inconnu, project_key
            non résolu.
    """
    fields_md = _split_fields(text)

    summary = fields_md.get("Summary", "").strip()
    if not summary:
        raise ValueError("Champ `# Summary` obligatoire et non vide.")

    description_md = fields_md.get("Description")
    if description_md is None:
        raise ValueError("Champ `# Description` obligatoire.")

    project_key = fields_md.get("Project") or defaults.get("project_key", "")
    if not project_key:
        raise ValueError(
            "`# Project` absent et `project_key` non défini dans la config. "
            "Utiliser `Tools → Alfaco → Atlassian → Sélectionner projet Jira` "
            "ou ajouter `# Project\\n<KEY>` au template."
        )

    issue_type = fields_md.get("Type") or defaults.get("type", "Task")
    priority = fields_md.get("Priority") or defaults.get("priority", "High")

    labels_csv = fields_md.get("Labels")
    if labels_csv:
        labels = [s.strip() for s in labels_csv.split(",") if s.strip()]
    else:
        labels = list(defaults.get("labels", []))

    startdate = fields_md.get("Startdate") or defaults.get("startdate", "")
    duedate = fields_md.get("Duedate") or defaults.get("duedate", "")

    return {
        "fields": {
            "summary": summary,
            "description": _markdown_to_adf(description_md),
            "startdate": startdate,
            "duedate": duedate,
            "issuetype": {"name": issue_type, "subtask": False},
            "project": {"key": project_key},
            "priority": {"name": priority},
            "labels": labels,
        }
    }
```

- [ ] **Step 4: Vérifier GREEN**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: 35 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown-to-adf): parse_markdown_jira_template + validation"
```

---

### Task 11: Snippet template Markdown

**Files:**
- Create: `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown`

- [ ] **Step 1: Créer le snippet**

Contenu de `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown` :

```xml
<snippet>
	<content><![CDATA[
# Summary
${1:à compléter}

# Project
${jira_key}

# Type
Task

# Priority
High

# Labels
important, urgent

# Startdate
${startdate}

# Duedate
${duedate}

# Description

${2:à compléter}
$0
]]></content>
	<!-- Pas de tabTrigger : insertion via la commande init_markdown_jira uniquement. -->
</snippet>
```

- [ ] **Step 2: Vérifier qu'il est versionné**

Run: `git status`
Expected: nouveau fichier non staged.

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown
git commit -m "feat(atlassian): snippet template Markdown pour init_markdown_jira"
```

---

### Task 12: InitMarkdownJiraCommand

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/init_markdown_jira.py`

- [ ] **Step 1: Implémenter la commande**

Contenu de `plugins/AlfacoAtlassian/commands/init_markdown_jira.py` :

```python
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
            "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown",
        )
        args["startdate"] = today.strftime("%Y-%m-%d")
        args["duedate"] = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        args["jira_key"] = _atlassian_plugin.config.get("project_key", "")

        _atlassian_plugin.log.info(
            f"init_markdown_jira : template inséré (project_key={args['jira_key']!r})"
        )
        sublime.status_message("AlfacoAtlassian : template Markdown inséré")
        new_view.run_command("insert_snippet", args)
```

- [ ] **Step 2: Vérifier la suite globale (la commande importe sublime mais ne s'instancie pas pendant pytest)**

Run: `make test`
Expected: 35 tests markdown_to_adf + 48 autres = 83 passed (le nouveau fichier `init_markdown_jira.py` est ignoré par pytest car non importé).

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/init_markdown_jira.py
git commit -m "feat(atlassian): InitMarkdownJiraCommand (insertion template)"
```

---

### Task 13: CreateJiraFromMarkdownCommand

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py`

- [ ] **Step 1: Implémenter la commande**

Contenu de `plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py` :

```python
# -*- coding: utf-8 -*-
"""Lit un buffer Markdown, le parse via parse_markdown_jira_template, et POST.

Symétrique à create_jira_issue mais source = Markdown. La conversion
description→ADF est faite par le parser, pas par wrap_description_as_adf.
"""
import json as _json
import time
from datetime import datetime, timedelta

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest
from AlfacoLib.io import save_file, build_response_path, build_payload_path
from AlfacoLib.markdown_to_adf import parse_markdown_jira_template


class CreateJiraFromMarkdownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        text = self.view.substr(sublime.Region(0, self.view.size()))

        today = datetime.now()
        defaults = {
            "project_key": cfg.get("project_key", ""),
            "startdate": today.strftime("%Y-%m-%d"),
            "duedate": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "type": "Task",
            "priority": "High",
            "labels": ["important", "urgent"],
        }

        try:
            payload = parse_markdown_jira_template(text, defaults)
        except ValueError as e:
            _atlassian_plugin.log.error(f"parse_markdown_jira_template : {e}")
            sublime.error_message(f"AlfacoAtlassian (Markdown) : {e}")
            return

        contenu = _json.dumps(payload, ensure_ascii=False, indent=4)
        url = cfg.base_url() + "issue/"
        headers = cfg.get("headers", {"Content-type": "application/json", "Accept": "application/json"})
        _atlassian_plugin.log.info(f"POST {url} ({len(contenu)} bytes) [from Markdown]")
        sublime.status_message(f"AlfacoAtlassian : POST {url}…")

        response = call_rest(
            url,
            body=contenu,
            auth=cfg.jira_auth(),
            headers=headers,
            verb="POST",
            verify=cfg.get("tls_verify", True),
        )

        _atlassian_plugin.log.info(f"POST {url} → {response.status_code}")
        if response.status_code >= 400:
            _atlassian_plugin.log.error(
                f"POST {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.status_message(
                f"AlfacoAtlassian : POST {url} → {response.status_code} (voir buffer réponse)"
            )

        new_view = self.view.window().new_file()
        new_view.set_name(f"Jira response {response.status_code}")
        new_view.run_command("insert", {"characters": response.text})

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            try:
                jira_key = response.json()["key"]
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(
                    f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})"
                )
                sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
            except (KeyError, ValueError):
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (code {response.status_code}) — payload non sauvegardé."
                )
```

- [ ] **Step 2: Vérifier la suite globale**

Run: `make test`
Expected: 83 passed (idem qu'à la tâche 12).

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py
git commit -m "feat(atlassian): CreateJiraFromMarkdownCommand (parse + POST)"
```

---

### Task 14: Wire des nouvelles commandes dans plugin.py

**Files:**
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1: Ajouter les 2 imports en fin de fichier**

Ajouter après la ligne `from AlfacoAtlassian.commands.set_jira_project_in_snippet import SetJiraProjectInSnippetCommand  # noqa: F401` :

```python
from AlfacoAtlassian.commands.init_markdown_jira import InitMarkdownJiraCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.create_jira_from_markdown import CreateJiraFromMarkdownCommand  # noqa: E402, F401
```

- [ ] **Step 2: Vérifier la suite**

Run: `make test`
Expected: 83 passed.

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/plugin.py
git commit -m "feat(atlassian): wire les 2 nouvelles commandes Markdown dans plugin.py"
```

---

### Task 15: Keymaps — 3 OS

**Files:**
- Modify: `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`

- [ ] **Step 1: Linux — ajouter 2 raccourcis**

Mettre à jour `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap` :

```json
[
    {
        "keys": ["ctrl+shift+j"],
        "command": "init_json_jira",
        "args": { "name": "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet" }
    },
    {
        "keys": ["ctrl+alt+m"],
        "command": "init_markdown_jira"
    },
    {
        "keys": ["alt+m"],
        "command": "create_jira_from_markdown"
    },
    {
        "keys": ["f2"],
        "command": "run_macro_file",
        "args": { "file": "Packages/AlfacoAtlassian/macros/addjira.sublime-macro" }
    }
]
```

- [ ] **Step 2: Windows — ajouter 2 raccourcis**

Mettre à jour `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap` :

```json
[
    { "keys": ["ctrl+alt+j"], "command": "pretty_json" },
    { "keys": ["ctrl+j", "ctrl+l"], "command": "select_jira_project" },
    {
        "keys": ["ctrl+shift+j"],
        "command": "init_json_jira",
        "args": { "name": "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet" }
    },
    {
        "keys": ["ctrl+alt+m"],
        "command": "init_markdown_jira"
    },
    {
        "keys": ["alt+m"],
        "command": "create_jira_from_markdown"
    },
    {
        "keys": ["ctrl+alt+w"],
        "command": "insert_snippet",
        "args": { "contents": "{\"fields\":${0:$SELECTION}}" }
    },
    { "keys": ["alt+j"], "command": "create_jira_issue" }
]
```

- [ ] **Step 3: macOS — ajouter 2 raccourcis**

Mettre à jour `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap` :

```json
[
    {
        "keys": ["super+shift+j"],
        "command": "init_json_jira",
        "args": { "name": "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet" }
    },
    {
        "keys": ["super+alt+m"],
        "command": "init_markdown_jira"
    },
    {
        "keys": ["super+shift+m"],
        "command": "create_jira_from_markdown"
    }
]
```

- [ ] **Step 4: Vérifier la suite**

Run: `make test`
Expected: 83 passed (les keymaps ne sont pas testés).

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoAtlassian/Default*sublime-keymap
git commit -m "feat(atlassian): keymaps Markdown (Ctrl+Alt+M init / Alt+M POST × 3 OS)"
```

---

### Task 16: Menus Main + Context

**Files:**
- Modify: `plugins/AlfacoAtlassian/Main.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Context.sublime-menu`

- [ ] **Step 1: Main.sublime-menu — ajouter sous Tools → Alfaco → Atlassian**

Lire le fichier courant avec `cat plugins/AlfacoAtlassian/Main.sublime-menu` pour vérifier l'indentation, puis insérer après l'entrée "Initialiser JSON Jira" :

```json
{ "caption": "Initialiser Markdown Jira", "command": "init_markdown_jira" },
{ "caption": "Créer ticket Jira (depuis Markdown)", "command": "create_jira_from_markdown" },
```

L'entrée s'ajoute dans le tableau `children` du sous-menu `alfaco-atlassian`, après `init_json_jira`.

- [ ] **Step 2: Context.sublime-menu — ajouter au menu clic-droit**

Lire `cat plugins/AlfacoAtlassian/Context.sublime-menu` puis ajouter dans le tableau `children` après l'entrée existante "créer ticket Jira" :

```json
{ "caption": "créer ticket Jira (depuis Markdown)", "command": "create_jira_from_markdown" },
{ "caption": "init Markdown Jira", "command": "init_markdown_jira" }
```

- [ ] **Step 3: Vérifier la suite**

Run: `make test`
Expected: 83 passed.

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoAtlassian/Main.sublime-menu plugins/AlfacoAtlassian/Context.sublime-menu
git commit -m "feat(atlassian): menus Tools + clic-droit pour les commandes Markdown"
```

---

### Task 17: Documentation

**Files:**
- Modify: `docs/plugins/alfaco-atlassian.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: docs/plugins/alfaco-atlassian.md — ajouter une section "Workflow Markdown"**

Avant la section "## Raccourcis", ajouter :

```markdown
## Workflow Markdown (alternatif au JSON)

Depuis la v0.5.0, un second flux permet de créer un ticket depuis un buffer Markdown au lieu d'un buffer JSON.

`Ctrl+Alt+M` (Linux/Win) / `Cmd+Alt+M` (Mac) → ouvre un buffer Markdown scratch avec le template :

\`\`\`markdown
# Summary
…

# Project
SDAL

# Type
Task

# Priority
High

# Labels
important, urgent

# Startdate
2026-05-27

# Duedate
2026-06-06

# Description

…
\`\`\`

Tab navigue summary → description. Une fois rempli, `Alt+M` (Linux/Win) / `Cmd+Shift+M` (Mac) parse, convertit le corps Markdown en ADF (paragraphes, headings, listes, **emphase**, `code`, [liens](url), code blocks) et POST.

Champs réservés : `Summary`, `Project`, `Type`, `Priority`, `Labels`, `Startdate`, `Duedate`, `Description`. Un `# UnknownField` produit une erreur explicite. `Summary` et `Description` sont obligatoires ; les autres ont des fallbacks (project_key courant, today + 10 jours, etc.).

Détails et limites du parser : voir `plugins/AlfacoLib/markdown_to_adf.py` (non supporté MVP : tables, images, blockquotes, listes imbriquées, strikethrough → texte brut).

```

- [ ] **Step 2: docs/plugins/alfaco-atlassian.md — étendre le tableau Raccourcis**

Dans le tableau "## Raccourcis", ajouter après les lignes existantes :

```markdown
| `Ctrl+Alt+M` | Linux / Windows | `init_markdown_jira` — buffer Markdown scratch + template pré-rempli |
| `Cmd+Alt+M` | macOS | idem |
| `Alt+M` | Linux / Windows | `create_jira_from_markdown` — parse + POST |
| `Cmd+Shift+M` | macOS | idem |
```

- [ ] **Step 3: CLAUDE.md — mention dans "What this is"**

Trouver la ligne :

```
| `AlfacoAtlassian` | Jira/Confluence REST workflows: select org/project, create issues, init JSON snippets. |
```

et la remplacer par :

```
| `AlfacoAtlassian` | Jira/Confluence REST workflows: select org/project, create issues depuis JSON ou Markdown (templates). |
```

- [ ] **Step 4: Vérifier**

Run: `make test`
Expected: 83 passed (la doc n'est pas testée).

- [ ] **Step 5: Commit**

```bash
git add docs/plugins/alfaco-atlassian.md CLAUDE.md
git commit -m "docs(atlassian): documente le flux Markdown (template + raccourcis)"
```

---

### Task 18: PR feat/markdown-to-jira → development → main

**Files:** aucune modif code, juste la PR.

- [ ] **Step 1: Push la branche**

```bash
git push -u origin feat/markdown-to-jira
```

- [ ] **Step 2: Ouvrir la PR vers development**

```bash
gh pr create --base development --head feat/markdown-to-jira \
    --title "feat(atlassian): création de tickets Jira depuis Markdown" \
    --body "$(cat <<'EOF'
## Summary

Implémente la spec [2026-05-27-markdown-to-jira-design.md](../blob/development/docs/superpowers/specs/2026-05-27-markdown-to-jira-design.md).

- Nouveau module pur `AlfacoLib/markdown_to_adf.py` (parser regex stdlib, ~250 lignes, 35 tests TDD)
- `parse_markdown_jira_template(text, defaults) → payload` : H1 = champs, Description capture jusqu'EOF
- Conversion Markdown → ADF : paragraphes, headings (h1-h6), listes (bullet/ordered), **bold**, *italic*, \`code\`, code blocks (avec language), [links](url)
- 2 nouvelles commandes : `InitMarkdownJiraCommand` (insertion template) + `CreateJiraFromMarkdownCommand` (parse + POST)
- Snippet `jira.sublime-snippet-markdown` avec tab stops summary → description
- Keymaps : Ctrl+Alt+M (insert) / Alt+M (POST) × Linux+Windows, Cmd+Alt+M / Cmd+Shift+M × Mac
- Menus : Tools → Alfaco → Atlassian + clic-droit
- Doc plugin + CLAUDE.md mis à jour

## Tests

\`\`\`
make test
83 passed (48 existants + 35 nouveaux pour markdown_to_adf)
\`\`\`

## Validation manuelle restante

- [ ] Ctrl+Alt+M ouvre buffer Markdown avec template rempli (project_key, dates)
- [ ] Tab navigue summary → description
- [ ] Alt+M sur template valide → ticket créé
- [ ] Alt+M sur template avec champ inconnu → error_message explicite
- [ ] Alt+M sur buffer non-template → error_message (Summary manquant)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Auto-merge vers development**

```bash
gh pr merge --merge --auto --delete-branch
```

- [ ] **Step 4: Cascade development → main**

```bash
git checkout development
git pull
gh pr create --base main --head development \
    --title "feat: création tickets Jira depuis Markdown" \
    --body "Propage la PR précédente vers main."
gh pr merge --merge --auto
```

---

## Self-Review Notes

**Couverture spec :**
- Format template (H1 + Description→EOF) : Task 9
- 8 champs réservés + validation : Task 9 (constants), Task 10 (validation)
- Conversion riche MD→ADF : Tasks 2-8
- 2 commandes symétriques : Tasks 12, 13
- Snippet : Task 11
- Keymaps 3 OS : Task 15
- Menus : Task 16
- Doc + CLAUDE.md : Task 17
- Wire dans plugin.py : Task 14
- API v2 fallback (string brute) : non implémenté explicitement, mais `parse_markdown_jira_template` génère toujours ADF — pour v2 le payload contiendra description ADF, Jira v2 l'accepte comme dict (à valider en manuel). Si v2 refuse : ajouter un branch `if api_rest_version != "3": fields["description"] = description_md` dans `CreateJiraFromMarkdownCommand` post-merge si besoin.

**Cohérence types/noms :**
- `_parse_inline` cohérent entre tasks 2-5.
- `_markdown_to_adf` cohérent tasks 6-8.
- `_split_fields` cohérent task 9, consommé task 10.
- `parse_markdown_jira_template` cohérent task 10, consommé task 13.
- `KNOWN_FIELDS` task 9, consommé pour validation task 10.

**Pas de placeholder.**

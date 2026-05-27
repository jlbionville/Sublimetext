"""Tests du parser Markdown → Jira (ADF)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.markdown_to_adf import _parse_inline  # noqa: E402


def test_parse_inline_plain_text():
    """Texte sans marks → un seul text node sans marks."""
    assert _parse_inline("hello world") == [
        {"type": "text", "text": "hello world"}
    ]


def test_parse_inline_empty_string():
    assert _parse_inline("") == []


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

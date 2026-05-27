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

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

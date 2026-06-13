"""Tests des E/S snippets et de la résolution de config (engine)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from AlfacoAwsCli import engine  # noqa: E402
from AlfacoAwsCli.constants import DEFAULT_PLACEHOLDER_MODE  # noqa: E402
from AlfacoAwsCli.domain import Template  # noqa: E402


class _Settings:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)


# ── slugify_filename ───────────────────────────────────────────────────────


def test_slugify_basic():
    assert engine.slugify_filename("S3 — URL présignée") == "s3-url-presignee"


def test_slugify_empty_falls_back():
    assert engine.slugify_filename("???") == "snippet"


# ── build_snippet_xml ↔ parse_snippet_file (round-trip) ─────────────────────


def test_build_then_parse_round_trip(tmp_path):
    xml = engine.build_snippet_xml("aws s3 ls s3://${bucket}", "S3 — liste")
    path = tmp_path / "s3-liste.sublime-snippet"
    path.write_text(xml, encoding="utf-8")
    tpl = engine.parse_snippet_file(str(path))
    assert tpl is not None
    assert tpl.caption == "S3 — liste"
    assert tpl.command == "aws s3 ls s3://${bucket}"
    assert tpl.source == Template.SOURCE_SNIPPET


def test_build_snippet_xml_preserves_cdata_close_sequence(tmp_path):
    # une séquence ]]> dans le contenu ne doit pas casser le CDATA
    content = "echo a]]>b"
    xml = engine.build_snippet_xml(content, "edge")
    path = tmp_path / "edge.sublime-snippet"
    path.write_text(xml, encoding="utf-8")
    assert engine.parse_snippet_file(str(path)).command == content


def test_parse_snippet_file_caption_falls_back_to_filename(tmp_path):
    path = tmp_path / "my-cmd.sublime-snippet"
    path.write_text("<snippet><content><![CDATA[aws s3 ls]]></content></snippet>", encoding="utf-8")
    assert engine.parse_snippet_file(str(path)).caption == "my-cmd"


def test_parse_snippet_file_invalid_returns_none(tmp_path):
    path = tmp_path / "broken.sublime-snippet"
    path.write_text("<snippet><content></content></snippet>", encoding="utf-8")
    assert engine.parse_snippet_file(str(path)) is None


# ── load_snippet_templates ─────────────────────────────────────────────────


def test_load_snippet_templates_reads_dir_sorted(tmp_path):
    (tmp_path / "b.sublime-snippet").write_text(
        "<snippet><content><![CDATA[aws b]]></content><description>B</description></snippet>",
        encoding="utf-8",
    )
    (tmp_path / "a.sublime-snippet").write_text(
        "<snippet><content><![CDATA[aws a]]></content><description>A</description></snippet>",
        encoding="utf-8",
    )
    (tmp_path / "ignore.txt").write_text("not a snippet", encoding="utf-8")
    settings = _Settings({"snippet_directories": [str(tmp_path)]})
    templates = engine.load_snippet_templates(settings)
    assert [t.caption for t in templates] == ["A", "B"]


def test_load_snippet_templates_missing_dir_ignored():
    settings = _Settings({"snippet_directories": ["/n/o/p/e"]})
    assert engine.load_snippet_templates(settings) == []


# ── resolve_mode ───────────────────────────────────────────────────────────


def test_resolve_mode_valid():
    assert engine.resolve_mode(_Settings({"placeholder_mode": "guided"})) == "guided"


def test_resolve_mode_invalid_falls_back_to_default():
    assert engine.resolve_mode(_Settings({"placeholder_mode": "bogus"})) == DEFAULT_PLACEHOLDER_MODE


# ── expand_directory ───────────────────────────────────────────────────────


def test_expand_directory_user_home():
    expanded = engine.expand_directory("~/snips")
    assert "~" not in expanded and expanded.endswith("snips")

"""Tests des helpers IO."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.io import save_file, read_file, build_response_path, build_payload_path  # noqa: E402


def test_save_and_read_roundtrip(tmp_path):
    f = tmp_path / "out.txt"
    save_file("hello é à", f)
    assert read_file(f) == "hello é à"


def test_save_file_creates_parent_dirs(tmp_path):
    f = tmp_path / "deep" / "nested" / "out.txt"
    save_file("x", f)
    assert f.read_text(encoding="utf-8") == "x"


def test_build_response_path_uses_os_join(tmp_path):
    result = build_response_path(tmp_path, timestamp="20260508-120000")
    assert result == tmp_path / "error_api_call_20260508-120000.html"


def test_build_payload_path_uses_jira_key(tmp_path):
    result = build_payload_path(tmp_path, jira_key="BUS-42")
    assert result == tmp_path / "BUS-42.json"

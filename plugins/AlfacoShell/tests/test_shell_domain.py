"""Tests du domain pur d'AlfacoShell — exécutables hors Sublime : pytest."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from AlfacoShell.constants import DEFAULT_EXEC_BY_PLATFORM  # noqa: E402
from AlfacoShell.domain import format_result, prettify, resolve_exec_argv  # noqa: E402


class _Cfg(dict):
    """Stub compatible sublime.Settings.get(key, default)."""

    def get(self, key, default=None):
        return super().get(key, default)


# ── resolve_exec_argv : défauts par plateforme ──────────────────────────────

def test_resolve_default_windows():
    argv = resolve_exec_argv("aws s3 ls", _Cfg(), "windows")
    assert argv == DEFAULT_EXEC_BY_PLATFORM["windows"] + ["aws s3 ls"]


def test_resolve_default_osx():
    argv = resolve_exec_argv("aws s3 ls", _Cfg(), "osx")
    assert argv == ["/bin/zsh", "-lc", "aws s3 ls"]


def test_resolve_default_linux():
    argv = resolve_exec_argv("aws s3 ls", _Cfg(), "linux")
    assert argv == ["bash", "-lc", "aws s3 ls"]


def test_resolve_unknown_platform_falls_back_to_linux():
    argv = resolve_exec_argv("echo hi", _Cfg(), "plan9")
    assert argv == ["bash", "-lc", "echo hi"]


# ── resolve_exec_argv : précédence des overrides ────────────────────────────

def test_exec_by_platform_overrides_default():
    cfg = _Cfg(exec_by_platform={"osx": ["bash", "-lc"]})
    argv = resolve_exec_argv("ls", cfg, "osx")
    assert argv == ["bash", "-lc", "ls"]


def test_exec_by_platform_missing_key_uses_default():
    # override fourni mais sans la clé de l'OS courant → défaut intégré
    cfg = _Cfg(exec_by_platform={"windows": ["wsl.exe", "-e", "bash", "-c"]})
    argv = resolve_exec_argv("ls", cfg, "linux")
    assert argv == ["bash", "-lc", "ls"]


def test_exec_prefix_overrides_everything():
    cfg = _Cfg(
        exec_prefix=["wsl.exe", "-e", "bash", "-c"],
        exec_by_platform={"osx": ["/bin/zsh", "-lc"]},
    )
    argv = resolve_exec_argv("ls", cfg, "osx")
    assert argv == ["wsl.exe", "-e", "bash", "-c", "ls"]


# ── prettify ────────────────────────────────────────────────────────────────

def test_prettify_formats_valid_json():
    out = prettify('{"a":1}')
    assert json.loads(out) == {"a": 1}
    assert "\n" in out  # indenté


def test_prettify_passes_through_non_json():
    assert prettify("plain text") == "plain text"


def test_prettify_empty_returns_input():
    assert prettify("   ") == "   "


# ── format_result ────────────────────────────────────────────────────────────

def test_format_result_includes_exit_code_and_stderr():
    res = format_result('{"k":1}', "warn", 2)
    assert "--- exit code: 2 ---" in res
    assert "--- stderr ---" in res
    assert '"k": 1' in res  # corps prettifié


def test_format_result_omits_stderr_when_empty():
    res = format_result("ok", "", 0)
    assert "--- stderr ---" not in res
    assert res.endswith("--- exit code: 0 ---")


def test_format_result_omits_empty_body():
    res = format_result("   ", "", 0)
    assert res == "--- exit code: 0 ---"

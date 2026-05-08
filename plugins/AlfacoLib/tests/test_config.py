"""Tests de AlfacoLib.config.Configuration."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.config import Configuration  # noqa: E402


def _settings_with(values):
    """Renvoie un objet façon sublime.Settings exposant get/has."""
    s = MagicMock()
    s.get = lambda key, default=None: values.get(key, default)
    s.has = lambda key: key in values
    return s


def test_get_returns_default_when_absent():
    cfg = Configuration([])
    assert cfg.get("missing", default="X") == "X"


def test_set_then_get_returns_runtime_value():
    cfg = Configuration([])
    cfg.set("project_key", "BUS")
    assert cfg.get("project_key") == "BUS"


def test_get_reads_from_loaded_settings_in_order(monkeypatch):
    layer1 = _settings_with({"shared_key": "from-1", "only-1": "v1"})
    layer2 = _settings_with({"shared_key": "from-2", "only-2": "v2"})
    monkeypatch.setattr(
        "AlfacoLib.config.sublime.load_settings",
        lambda name: layer1 if name == "first.sublime-settings" else layer2,
    )
    cfg = Configuration(["first.sublime-settings", "second.sublime-settings"])
    assert cfg.get("shared_key") == "from-1"
    assert cfg.get("only-1") == "v1"
    assert cfg.get("only-2") == "v2"


def test_runtime_set_overrides_loaded(monkeypatch):
    layer = _settings_with({"k": "loaded"})
    monkeypatch.setattr("AlfacoLib.config.sublime.load_settings", lambda _: layer)
    cfg = Configuration(["x.sublime-settings"])
    assert cfg.get("k") == "loaded"
    cfg.set("k", "runtime")
    assert cfg.get("k") == "runtime"


def test_jira_auth_returns_login_password_tuple(monkeypatch):
    layer = _settings_with({"jira_login": "alice@x", "jira_password": "tok"})
    monkeypatch.setattr("AlfacoLib.config.sublime.load_settings", lambda _: layer)
    cfg = Configuration(["x.sublime-settings"])
    assert cfg.jira_auth() == ("alice@x", "tok")


def test_base_url_uses_org_and_version(monkeypatch):
    layer = _settings_with({"default_organisation": "myorg", "api_rest_version": "3"})
    monkeypatch.setattr("AlfacoLib.config.sublime.load_settings", lambda _: layer)
    cfg = Configuration(["x.sublime-settings"])
    assert cfg.base_url() == "https://myorg.atlassian.net/rest/api/3/"


def test_base_url_version_override():
    cfg = Configuration([])
    cfg.set("default_organisation", "acme")
    assert cfg.base_url(version="2") == "https://acme.atlassian.net/rest/api/2/"

"""Tests de détection du dossier Packages/ Sublime."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.deploy import detect_packages_dir, _is_wsl  # noqa: E402


def test_detect_packages_dir_via_env(monkeypatch):
    monkeypatch.setenv("SUBLIME_PACKAGES_DIR", "/tmp/fake/Packages")
    assert detect_packages_dir() == Path("/tmp/fake/Packages")


def test_detect_packages_dir_macos(monkeypatch):
    monkeypatch.delenv("SUBLIME_PACKAGES_DIR", raising=False)
    with patch("tools.deploy.platform.system", return_value="Darwin"):
        result = detect_packages_dir()
    assert result == Path.home() / "Library/Application Support/Sublime Text/Packages"


def test_detect_packages_dir_windows(monkeypatch):
    monkeypatch.delenv("SUBLIME_PACKAGES_DIR", raising=False)
    monkeypatch.setenv("APPDATA", "C:\\Users\\bob\\AppData\\Roaming")
    with patch("tools.deploy.platform.system", return_value="Windows"):
        result = detect_packages_dir()
    assert "Sublime Text" in str(result)
    assert "Packages" in str(result)


def test_is_wsl_false_on_non_linux(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    assert _is_wsl() is False

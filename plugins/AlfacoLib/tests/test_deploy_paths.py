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


def test_detect_packages_dir_linux_st4(monkeypatch):
    """Sur Linux natif (hors WSL) avec ST4 installé, retourne le chemin ST4."""
    monkeypatch.delenv("SUBLIME_PACKAGES_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    expected = Path.home() / ".config/sublime-text/Packages"
    with patch("tools.deploy.platform.system", return_value="Linux"), \
         patch("tools.deploy._is_wsl", return_value=False), \
         patch.object(Path, "exists", lambda self: self == expected):
        result = detect_packages_dir()
    assert result == expected


def test_detect_packages_dir_wsl_with_cmd_exe(monkeypatch):
    """Sous WSL, le username Windows est résolu via cmd.exe (peut différer du USER WSL)."""
    monkeypatch.delenv("SUBLIME_PACKAGES_DIR", raising=False)
    with patch("tools.deploy.platform.system", return_value="Linux"), \
         patch("tools.deploy._is_wsl", return_value=True), \
         patch("tools.deploy._windows_username_from_wsl", return_value="jane"), \
         patch.object(Path, "exists", return_value=True):
        result = detect_packages_dir()
    assert result == Path("/mnt/c/Users/jane/AppData/Roaming/Sublime Text/Packages")


def test_detect_packages_dir_wsl_user_profile_missing(monkeypatch):
    """Sous WSL, si /mnt/c/Users/<user> n'existe pas, lever une erreur claire."""
    monkeypatch.delenv("SUBLIME_PACKAGES_DIR", raising=False)
    with patch("tools.deploy.platform.system", return_value="Linux"), \
         patch("tools.deploy._is_wsl", return_value=True), \
         patch("tools.deploy._windows_username_from_wsl", return_value="phantom"), \
         patch.object(Path, "exists", return_value=False):
        try:
            detect_packages_dir()
        except RuntimeError as e:
            assert "SUBLIME_PACKAGES_DIR" in str(e)
        else:
            assert False, "RuntimeError attendue"

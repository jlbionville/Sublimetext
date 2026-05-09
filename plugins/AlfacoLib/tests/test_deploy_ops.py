"""Tests des opérations link/install/uninstall/status."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.deploy import install, uninstall, status  # noqa: E402


def _make_plugin(monorepo: Path, name: str) -> Path:
    plugin = monorepo / "plugins" / name
    (plugin / "tests").mkdir(parents=True)
    (plugin / "plugin.py").write_text("# fake plugin\n")
    (plugin / "tests" / "test_x.py").write_text("def test_x(): pass\n")
    (plugin / "__pycache__").mkdir()
    (plugin / "__pycache__" / "x.pyc").write_text("")
    return plugin


def test_install_copies_without_excluded_dirs(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoLib")
    packages = tmp_path / "Packages"
    packages.mkdir()

    done = install(monorepo, packages)
    assert done == ["AlfacoLib"]
    assert (packages / "AlfacoLib" / "plugin.py").exists()
    assert not (packages / "AlfacoLib" / "tests").exists()
    assert not (packages / "AlfacoLib" / "__pycache__").exists()


def test_uninstall_removes_plugin(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoLib")
    packages = tmp_path / "Packages"
    packages.mkdir()
    install(monorepo, packages)

    done = uninstall(monorepo, packages)
    assert done == ["AlfacoLib"]
    assert not (packages / "AlfacoLib").exists()


def test_status_reports_correct_modes(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoLib")
    _make_plugin(monorepo, "AlfacoEditing")
    packages = tmp_path / "Packages"
    packages.mkdir()
    install(monorepo, packages, only="AlfacoLib")

    s = status(monorepo, packages)
    assert s == {"AlfacoLib": "copy", "AlfacoEditing": "absent"}


def test_install_only_one_plugin(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoLib")
    _make_plugin(monorepo, "AlfacoEditing")
    packages = tmp_path / "Packages"
    packages.mkdir()

    done = install(monorepo, packages, only="AlfacoEditing")
    assert done == ["AlfacoEditing"]
    assert (packages / "AlfacoEditing").exists()
    assert not (packages / "AlfacoLib").exists()

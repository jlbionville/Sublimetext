"""Tests des opérations link/install/uninstall/status/init-config."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.deploy import install, uninstall, status, init_config  # noqa: E402


def _make_plugin(monorepo: Path, name: str, with_template: bool = False,
                 with_metadata: bool = False, with_settings: bool = False) -> Path:
    plugin = monorepo / "plugins" / name
    (plugin / "tests").mkdir(parents=True)
    (plugin / "plugin.py").write_text("# fake plugin\n")
    (plugin / "tests" / "test_x.py").write_text("def test_x(): pass\n")
    (plugin / "__pycache__").mkdir()
    (plugin / "__pycache__" / "x.pyc").write_text("")
    if with_settings:
        (plugin / f"{name.lower()}.sublime-settings").write_text(
            '{ "default_key": "default_value" }\n'
        )
    if with_template:
        tpl = plugin / "templates" / "User"
        tpl.mkdir(parents=True)
        (tpl / f"{name.lower()}.sublime-settings").write_text(
            '{ "fake_key": "fake_value" }\n'
        )
    if with_metadata:
        (plugin / "package-metadata.json").write_text(
            '{ "name": "' + name + '", "version": "0.1.0" }\n'
        )
    return plugin


def test_install_excludes_package_metadata_json(tmp_path):
    """package-metadata.json est l'indicateur Package Control « ce paquet est géré par moi ».
    Si présent ET absent de installed_packages, PC le supprime au démarrage. On ne veut
    pas le déployer : Sublime ouvre alors le plugin comme un dossier manuel (jamais touché)."""
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoLib", with_metadata=True)
    packages = tmp_path / "Packages"
    packages.mkdir()

    install(monorepo, packages)
    assert (packages / "AlfacoLib" / "plugin.py").exists()
    assert not (packages / "AlfacoLib" / "package-metadata.json").exists()


def test_install_excludes_package_settings(tmp_path):
    """Le fichier de settings du package n'est pas déployé : la config vit
    dans <Packages>/User/ (posé par init-config), jamais écrasé par install."""
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoAtlassian", with_settings=True)
    packages = tmp_path / "Packages"
    packages.mkdir()

    install(monorepo, packages)
    assert (packages / "AlfacoAtlassian" / "plugin.py").exists()
    assert not (packages / "AlfacoAtlassian" / "alfacoatlassian.sublime-settings").exists()


def test_install_seeds_user_config_skip_if_exists(tmp_path):
    """install seed <Packages>/User/ depuis le template (skip-if-exists) :
    1er install crée le fichier User, les suivants ne l'écrasent jamais."""
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoAtlassian", with_template=True)
    packages = tmp_path / "Packages"
    packages.mkdir()

    install(monorepo, packages)
    user_file = packages / "User" / "alfacoatlassian.sublime-settings"
    assert user_file.exists()

    user_file.write_text('{ "jira_login": "me@x.io" }\n')
    install(monorepo, packages)
    assert "me@x.io" in user_file.read_text()


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


def test_install_excludes_templates_dir(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoAtlassian", with_template=True)
    packages = tmp_path / "Packages"
    packages.mkdir()

    install(monorepo, packages)
    assert (packages / "AlfacoAtlassian" / "plugin.py").exists()
    assert not (packages / "AlfacoAtlassian" / "templates").exists()


def test_init_config_copies_templates_to_user(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoAtlassian", with_template=True)
    _make_plugin(monorepo, "AlfacoEditing", with_template=True)
    packages = tmp_path / "Packages"
    packages.mkdir()

    ops = init_config(monorepo, packages)
    actions = sorted((a, p) for a, p, _ in ops)
    assert actions == [("copied", "AlfacoAtlassian"), ("copied", "AlfacoEditing")]
    assert (packages / "User" / "alfacoatlassian.sublime-settings").exists()
    assert (packages / "User" / "alfacoediting.sublime-settings").exists()


def test_init_config_skips_existing_files(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoAtlassian", with_template=True)
    packages = tmp_path / "Packages"
    (packages / "User").mkdir(parents=True)
    (packages / "User" / "alfacoatlassian.sublime-settings").write_text(
        '{ "user_filled": true }\n'
    )

    ops = init_config(monorepo, packages)
    assert ops == [("skipped", "AlfacoAtlassian", "alfacoatlassian.sublime-settings")]
    assert "user_filled" in (packages / "User" / "alfacoatlassian.sublime-settings").read_text()


def test_init_config_force_overwrites(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoAtlassian", with_template=True)
    packages = tmp_path / "Packages"
    (packages / "User").mkdir(parents=True)
    (packages / "User" / "alfacoatlassian.sublime-settings").write_text(
        '{ "user_filled": true }\n'
    )

    ops = init_config(monorepo, packages, force=True)
    assert ops == [("copied", "AlfacoAtlassian", "alfacoatlassian.sublime-settings")]
    assert "fake_key" in (packages / "User" / "alfacoatlassian.sublime-settings").read_text()


def test_init_config_creates_user_dir_if_missing(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoEditing", with_template=True)
    packages = tmp_path / "Packages"
    packages.mkdir()  # pas de User/

    init_config(monorepo, packages)
    assert (packages / "User" / "alfacoediting.sublime-settings").exists()


def test_init_config_no_template_no_op(tmp_path):
    monorepo = tmp_path / "repo"
    (monorepo / "plugins").mkdir(parents=True)
    _make_plugin(monorepo, "AlfacoLib", with_template=False)  # pas de templates/
    packages = tmp_path / "Packages"
    packages.mkdir()

    ops = init_config(monorepo, packages)
    assert ops == []

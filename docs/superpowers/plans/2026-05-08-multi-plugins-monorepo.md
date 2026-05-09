# Refactorisation monorepo multi-plugins — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer le package Sublime Text monolithique `Alfaco` en un monorepo qui produit 4 packages indépendants (`AlfacoLib`, `AlfacoAtlassian`, `AlfacoEditing`, `AlfacoCompletion`), avec outillage de déploiement multi-OS, tests pytest, et corrections des bugs documentés.

**Architecture:** Monorepo `plugins/` avec un sous-dossier par package Sublime déployable. `AlfacoLib` est un package Sublime sans commandes utilisateur, importé par les autres via `from AlfacoLib.config import Configuration`. Déploiement orchestré par `Makefile` + `tools/deploy.py` (link symbolique pour le dev, copie pour install propre, détection auto Linux/macOS/Windows/WSL). Tests pytest hors Sublime via stub du module `sublime`.

**Tech Stack:** Python 3.8 (plugin host Sublime Text 4), Sublime Text API, `requests`, `pytest`, `requests-mock`, `make`.

**Spec source:** `docs/superpowers/specs/2026-05-08-multi-plugins-monorepo-design.md`

---

## Convention pour ce plan

- **Chemins** relatifs à la racine du repo `/mnt/c/workspace/depots/Sublimetext/` sauf indication contraire.
- **Branche** : `refactor/multi-plugins`, créée depuis `development` à la Task 1.
- **Commits** : un par Task qui termine une unité fonctionnelle, message en français.
- **Validation manuelle Sublime** : explicite quand requise (Tasks 13, 16, 17, 20).
- **Code à copier verbatim** : montré en intégralité. **Code à déplacer sans modif** : indiqué par « copier intégralement de X vers Y », pas de duplication dans le plan.

---

## Phase A — Squelette (sans casser l'existant)

### Task 1: Branche de travail et squelette de dossiers

**Files:**
- Create: `plugins/.gitkeep`
- Create: `tools/.gitkeep`

- [ ] **Step 1: Créer la branche de travail**

```bash
git checkout development
git pull --ff-only origin development 2>/dev/null || true
git checkout -b refactor/multi-plugins
```

Expected: `Switched to a new branch 'refactor/multi-plugins'`

- [ ] **Step 2: Créer les dossiers `plugins/` et `tools/`**

```bash
mkdir -p plugins tools
touch plugins/.gitkeep tools/.gitkeep
```

- [ ] **Step 3: Vérifier l'état**

Run: `ls -la plugins tools`
Expected: chaque dossier contient un `.gitkeep`.

- [ ] **Step 4: Commit**

```bash
git add plugins/.gitkeep tools/.gitkeep
git commit -m "création des dossiers plugins/ et tools/ du monorepo"
```

---

### Task 2: `pyproject.toml` et stub pytest

**Files:**
- Create: `pyproject.toml`
- Create: `conftest.py` (à la racine du monorepo)

- [ ] **Step 1: Créer `pyproject.toml`**

```toml
[project]
name = "alfaco-monorepo"
version = "0.2.0"
description = "Monorepo des plugins Sublime Text Alfaco"
requires-python = ">=3.8"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "requests-mock>=1.11",
    "requests>=2.28",
]

[tool.pytest.ini_options]
testpaths = ["plugins"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
```

- [ ] **Step 2: Créer le stub `sublime` partagé**

Crée `conftest.py` à la racine :

```python
"""Stub du module Sublime Text pour les tests pytest hors Sublime."""
import sys
from unittest.mock import MagicMock

# Stub des modules Sublime utilisés par AlfacoLib et les plugins
sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
```

- [ ] **Step 3: Vérifier que pytest démarre sans erreur (collecte vide attendue)**

Run: `python -m pytest --collect-only`
Expected: `no tests ran`, code de retour 0 ou 5 (pas 1/2). Si pytest n'est pas installé : `pip install -e '.[dev]'` puis recommencer.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml conftest.py
git commit -m "ajout de pyproject.toml et stub sublime pour pytest"
```

---

### Task 3: `tools/deploy.py` — détection des chemins Sublime

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/deploy.py`
- Create: `plugins/AlfacoLib/tests/test_deploy_paths.py`

- [ ] **Step 1: Créer `tools/__init__.py` vide**

```bash
touch tools/__init__.py
```

- [ ] **Step 2: Créer `tools/deploy.py` minimal — détection d'OS et Packages dir**

```python
"""Outil de déploiement du monorepo Alfaco vers Sublime Text Packages/."""
from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def detect_packages_dir() -> Path:
    """Retourne le chemin du dossier Packages/ de Sublime Text.

    Ordre de résolution :
    1. Variable d'environnement SUBLIME_PACKAGES_DIR.
    2. Détection automatique selon l'OS / WSL.
    """
    env = os.environ.get("SUBLIME_PACKAGES_DIR")
    if env:
        return Path(env).expanduser()

    system = platform.system()
    if system == "Linux":
        if _is_wsl():
            user = os.environ.get("USER") or os.environ.get("USERNAME")
            if not user:
                raise RuntimeError(
                    "WSL détecté mais USER non défini. "
                    "Posez SUBLIME_PACKAGES_DIR=/mnt/c/Users/<user>/AppData/Roaming/Sublime Text/Packages"
                )
            return Path(f"/mnt/c/Users/{user}/AppData/Roaming/Sublime Text/Packages")
        st4 = Path.home() / ".config/sublime-text/Packages"
        st3 = Path.home() / ".config/sublime-text-3/Packages"
        return st4 if st4.exists() else st3
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Sublime Text/Packages"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA non défini sur Windows")
        return Path(appdata) / "Sublime Text/Packages"
    raise RuntimeError(f"OS non supporté : {system}")


def _is_wsl() -> bool:
    """Retourne True si l'environnement courant est WSL."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False
```

- [ ] **Step 3: Créer le test associé**

Crée `plugins/AlfacoLib/tests/__init__.py` vide :
```bash
mkdir -p plugins/AlfacoLib/tests
touch plugins/AlfacoLib/tests/__init__.py
```

Crée `plugins/AlfacoLib/tests/test_deploy_paths.py` :

```python
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
```

- [ ] **Step 4: Lancer les tests**

Run: `python -m pytest plugins/AlfacoLib/tests/test_deploy_paths.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/__init__.py tools/deploy.py plugins/AlfacoLib/tests/__init__.py plugins/AlfacoLib/tests/test_deploy_paths.py
git commit -m "tools/deploy.py : détection multi-OS du dossier Packages Sublime"
```

---

### Task 4: `tools/deploy.py` — opérations link / install / uninstall / status

**Files:**
- Modify: `tools/deploy.py` (ajouts)
- Create: `plugins/AlfacoLib/tests/test_deploy_ops.py`

- [ ] **Step 1: Ajouter les fonctions d'opération à `tools/deploy.py`**

Ajouter à la fin du fichier (après `_is_wsl`) :

```python
EXCLUDE_DURING_DEPLOY = {"tests", "__pycache__", ".pytest_cache", ".git"}


def _iter_plugins(monorepo_root: Path) -> list[Path]:
    plugins_dir = monorepo_root / "plugins"
    return sorted(p for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith("."))


def _filter_for_deploy(src: Path, name: str) -> bool:
    if name in EXCLUDE_DURING_DEPLOY:
        return False
    if name.endswith(".pyc"):
        return False
    return True


def _copy_plugin(src: Path, dst: Path) -> None:
    if dst.exists():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if not _filter_for_deploy(Path(d), n)])


def _link_plugin(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    try:
        os.symlink(src, dst, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Fallback Windows : junction
        if platform.system() == "Windows":
            os.system(f'mklink /J "{dst}" "{src}"')
        else:
            raise


def link(monorepo_root: Path, packages_dir: Path, only: str | None = None) -> list[str]:
    if _is_wsl():
        print("WSL détecté → mode 'install' (copie) forcé : NTFS ne suit pas les symlinks WSL.")
        return install(monorepo_root, packages_dir, only=only)
    done = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        _link_plugin(plugin, packages_dir / plugin.name)
        done.append(plugin.name)
    return done


def install(monorepo_root: Path, packages_dir: Path, only: str | None = None) -> list[str]:
    done = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        _copy_plugin(plugin, packages_dir / plugin.name)
        done.append(plugin.name)
    return done


def uninstall(monorepo_root: Path, packages_dir: Path, only: str | None = None) -> list[str]:
    done = []
    for plugin in _iter_plugins(monorepo_root):
        if only and plugin.name != only:
            continue
        dst = packages_dir / plugin.name
        if not dst.exists() and not dst.is_symlink():
            continue
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
        done.append(plugin.name)
    return done


def status(monorepo_root: Path, packages_dir: Path) -> dict[str, str]:
    out = {}
    for plugin in _iter_plugins(monorepo_root):
        dst = packages_dir / plugin.name
        if not dst.exists() and not dst.is_symlink():
            out[plugin.name] = "absent"
        elif dst.is_symlink():
            out[plugin.name] = "link"
        else:
            out[plugin.name] = "copy"
    return out
```

- [ ] **Step 2: Ajouter le CLI à la fin de `tools/deploy.py`**

```python
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="deploy")
    parser.add_argument("action", choices=["link", "install", "uninstall", "status"])
    parser.add_argument("--plugin", default=None, help="Cibler un seul plugin")
    parser.add_argument("--packages-dir", default=None)
    args = parser.parse_args()

    monorepo_root = Path(__file__).resolve().parents[1]
    packages_dir = Path(args.packages_dir).expanduser() if args.packages_dir else detect_packages_dir()

    if args.action == "status":
        for name, mode in status(monorepo_root, packages_dir).items():
            print(f"  {name:25s} {mode}")
        return 0
    if args.action == "link":
        done = link(monorepo_root, packages_dir, only=args.plugin)
    elif args.action == "install":
        done = install(monorepo_root, packages_dir, only=args.plugin)
    elif args.action == "uninstall":
        done = uninstall(monorepo_root, packages_dir, only=args.plugin)
    else:
        return 2
    print(f"{args.action}: {len(done)} plugin(s) → {', '.join(done) or '(aucun)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Créer les tests**

Crée `plugins/AlfacoLib/tests/test_deploy_ops.py` :

```python
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
```

- [ ] **Step 4: Lancer les tests**

Run: `python -m pytest plugins/AlfacoLib/tests/test_deploy_ops.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Tester le CLI manuellement (status)**

Run: `python tools/deploy.py status --packages-dir /tmp/fake-packages-that-doesnt-exist`
Expected: la commande s'exécute sans crash (ou affiche `(aucun)` si aucun plugin n'est encore créé).

- [ ] **Step 6: Commit**

```bash
git add tools/deploy.py plugins/AlfacoLib/tests/test_deploy_ops.py
git commit -m "tools/deploy.py : opérations link/install/uninstall/status"
```

---

### Task 5: `tools/new_plugin.py` et template de plugin

**Files:**
- Create: `tools/new_plugin.py`
- Create: `tools/templates/plugin/plugin.py`
- Create: `tools/templates/plugin/commands/__init__.py`
- Create: `tools/templates/plugin/tests/conftest.py`
- Create: `tools/templates/plugin/.python-version`
- Create: `tools/templates/plugin/package-metadata.json`
- Create: `tools/templates/plugin/README.md`

- [ ] **Step 1: Créer le squelette du template**

```bash
mkdir -p tools/templates/plugin/commands tools/templates/plugin/tests
```

- [ ] **Step 2: Créer `tools/templates/plugin/.python-version`**

Contenu (un seul caractère sur la ligne) :
```
3.8
```

- [ ] **Step 3: Créer `tools/templates/plugin/plugin.py`**

```python
# -*- coding: utf-8 -*-
"""Entry point du plugin {{NAME}}."""
import importlib
import sublime  # noqa: F401  (réservé pour usages futurs)

from AlfacoLib import config as _alfacolib_config

_LIB_MODULES = (_alfacolib_config,)

config = None


def plugin_loaded():
    global config
    for mod in _LIB_MODULES:
        importlib.reload(mod)
    config = _alfacolib_config.Configuration([
        "alfaco-{{name}}.sublime-settings",
        "Preferences.sublime-settings",
    ])
```

- [ ] **Step 4: Créer `tools/templates/plugin/commands/__init__.py`** (vide)

```bash
touch tools/templates/plugin/commands/__init__.py
```

- [ ] **Step 5: Créer `tools/templates/plugin/tests/conftest.py`**

```python
"""Stub sublime local au plugin (hérite du conftest racine)."""
```

- [ ] **Step 6: Créer `tools/templates/plugin/package-metadata.json`**

```json
{
    "name": "Alfaco{{NAME}}",
    "version": "0.2.0",
    "description": "Plugin Sublime Text {{NAME}} (suite Alfaco)",
    "sublime_text": ">=4000",
    "platforms": ["*"],
    "dependencies_alfaco": [
        { "name": "AlfacoLib", "version": ">=0.1.0,<1.0.0" }
    ]
}
```

- [ ] **Step 7: Créer `tools/templates/plugin/README.md`**

```markdown
# Alfaco{{NAME}}

Plugin Sublime Text — suite Alfaco.

## Installation

Depuis le monorepo : `make link PLUGIN=Alfaco{{NAME}}`.

## Documentation

Voir `docs/plugins/alfaco-{{name}}.md`.
```

- [ ] **Step 8: Créer `tools/new_plugin.py`**

```python
"""Scaffold un nouveau plugin Alfaco depuis tools/templates/plugin/."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def render_template(src: Path, dst: Path, name: str) -> None:
    name_lower = name.lower()
    if dst.exists():
        raise FileExistsError(f"{dst} existe déjà")
    shutil.copytree(src, dst)
    for path in dst.rglob("*"):
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            content = content.replace("{{NAME}}", name).replace("{{name}}", name_lower)
            path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="new-plugin")
    parser.add_argument("name", help="Nom du plugin sans préfixe (ex: Git → AlfacoGit)")
    args = parser.parse_args()

    monorepo_root = Path(__file__).resolve().parents[1]
    template = monorepo_root / "tools" / "templates" / "plugin"
    target = monorepo_root / "plugins" / f"Alfaco{args.name}"
    render_template(template, target, args.name)
    print(f"Plugin créé : {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 9: Tester le scaffold**

Run: `python tools/new_plugin.py Demo`
Expected: `Plugin créé : .../plugins/AlfacoDemo`. Vérifier `cat plugins/AlfacoDemo/package-metadata.json` → `Alfaco{{NAME}}` doit avoir été remplacé par `AlfacoDemo`.

- [ ] **Step 10: Nettoyer le plugin de test**

```bash
rm -rf plugins/AlfacoDemo
```

- [ ] **Step 11: Commit**

```bash
git add tools/new_plugin.py tools/templates/
git commit -m "tools/new_plugin.py : scaffold de nouveau plugin depuis template"
```

---

### Task 6: Makefile

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Créer le `Makefile`**

```makefile
PYTHON ?= python
PLUGIN ?=

.PHONY: link install uninstall relink status test new-plugin clean help

help:
	@echo "Cibles disponibles :"
	@echo "  link [PLUGIN=Nom]      symlinks plugins/* vers <Packages>/ (mode dev)"
	@echo "  install [PLUGIN=Nom]   copie plugins/* vers <Packages>/ (mode utilisateur)"
	@echo "  uninstall [PLUGIN=Nom] supprime <Packages>/Alfaco*"
	@echo "  relink                 uninstall + link"
	@echo "  status                 liste l'état de chaque plugin"
	@echo "  test                   pytest sur plugins/*/tests/"
	@echo "  new-plugin NAME=Foo    scaffold plugins/AlfacoFoo/"
	@echo "  clean                  supprime __pycache__/, .pytest_cache/"

link:
	$(PYTHON) tools/deploy.py link $(if $(PLUGIN),--plugin $(PLUGIN),)

install:
	$(PYTHON) tools/deploy.py install $(if $(PLUGIN),--plugin $(PLUGIN),)

uninstall:
	$(PYTHON) tools/deploy.py uninstall $(if $(PLUGIN),--plugin $(PLUGIN),)

relink: uninstall link

status:
	$(PYTHON) tools/deploy.py status

test:
	$(PYTHON) -m pytest

new-plugin:
	@if [ -z "$(NAME)" ]; then echo "Usage: make new-plugin NAME=Foo"; exit 1; fi
	$(PYTHON) tools/new_plugin.py $(NAME)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
```

- [ ] **Step 2: Tester `make help`**

Run: `make help`
Expected: la liste des cibles s'affiche.

- [ ] **Step 3: Tester `make test`**

Run: `make test`
Expected: les tests des Tasks 3-4 passent (8 tests).

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "Makefile avec cibles link/install/uninstall/status/test/new-plugin/clean"
```

---

### Task 7: `AlfacoLib` — `config.py` (TDD)

**Files:**
- Create: `plugins/AlfacoLib/__init__.py`
- Create: `plugins/AlfacoLib/config.py`
- Create: `plugins/AlfacoLib/tests/test_config.py`

- [ ] **Step 1: Créer `plugins/AlfacoLib/__init__.py`** (vide)

```bash
touch plugins/AlfacoLib/__init__.py
```

- [ ] **Step 2: Écrire les tests d'abord**

Crée `plugins/AlfacoLib/tests/test_config.py` :

```python
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
```

- [ ] **Step 3: Lancer les tests, vérifier qu'ils échouent**

Run: `python -m pytest plugins/AlfacoLib/tests/test_config.py -v`
Expected: tous FAIL avec `ImportError` ou `ModuleNotFoundError` (la classe `Configuration` n'existe pas encore).

- [ ] **Step 4: Implémenter `plugins/AlfacoLib/config.py`**

```python
# -*- coding: utf-8 -*-
"""Configuration partagée entre plugins Alfaco.

Empile plusieurs fichiers .sublime-settings + un dictionnaire runtime.
Aucun effet de bord sur Preferences.sublime-settings (contrairement au code legacy).
"""
from __future__ import annotations

import sublime


class Configuration:
    """Configuration empilée pour un plugin Alfaco."""

    def __init__(self, settings_files):
        self._settings_files = list(settings_files)
        self._loaded = None
        self._runtime = {}

    def _ensure_loaded(self):
        if self._loaded is None:
            self._loaded = [sublime.load_settings(name) for name in self._settings_files]
        return self._loaded

    def get(self, key, default=None):
        if key in self._runtime:
            return self._runtime[key]
        for layer in self._ensure_loaded():
            if layer.has(key):
                return layer.get(key)
        return default

    def set(self, key, value):
        self._runtime[key] = value

    def jira_auth(self):
        return (self.get("jira_login"), self.get("jira_password"))

    def base_url(self, version=None):
        org = self.get("default_organisation")
        ver = version if version is not None else self.get("api_rest_version", "2")
        return f"https://{org}.atlassian.net/rest/api/{ver}/"
```

- [ ] **Step 5: Relancer les tests**

Run: `python -m pytest plugins/AlfacoLib/tests/test_config.py -v`
Expected: 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/AlfacoLib/__init__.py plugins/AlfacoLib/config.py plugins/AlfacoLib/tests/test_config.py
git commit -m "AlfacoLib : Configuration empilée avec layer runtime"
```

---

### Task 8: `AlfacoLib` — `atlassian_client.py` (TDD)

**Files:**
- Create: `plugins/AlfacoLib/atlassian_client.py`
- Create: `plugins/AlfacoLib/tests/test_atlassian_client.py`

- [ ] **Step 1: Écrire les tests**

Crée `plugins/AlfacoLib/tests/test_atlassian_client.py` :

```python
"""Tests du wrapper REST Atlassian."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.atlassian_client import call_rest, list_projects  # noqa: E402

import requests_mock


def test_call_rest_get_passes_auth_headers_and_returns_json():
    auth = ("alice", "tok")
    with requests_mock.Mocker() as m:
        m.get("https://acme.atlassian.net/rest/api/3/issue/X-1", json={"key": "X-1"})
        result = call_rest(
            "https://acme.atlassian.net/rest/api/3/issue/X-1",
            body=None,
            auth=auth,
            headers={"Accept": "application/json"},
            verb="GET",
        )
    assert result.status_code == 200
    assert result.json() == {"key": "X-1"}
    assert m.last_request.headers["Authorization"].startswith("Basic ")


def test_call_rest_post_sends_body():
    with requests_mock.Mocker() as m:
        m.post("https://acme.atlassian.net/rest/api/3/issue/", json={"key": "X-2"}, status_code=201)
        result = call_rest(
            "https://acme.atlassian.net/rest/api/3/issue/",
            body='{"fields": {}}',
            auth=("alice", "tok"),
            headers={"Content-type": "application/json"},
            verb="POST",
        )
    assert result.status_code == 201
    assert m.last_request.text == '{"fields": {}}'


def test_call_rest_passes_timeout(monkeypatch):
    captured = {}
    def fake_request(verb, url, **kwargs):
        captured.update(kwargs)
        resp = MagicMock(status_code=200)
        return resp
    monkeypatch.setattr("AlfacoLib.atlassian_client.requests.request", fake_request)
    call_rest("u", body=None, auth=("a", "b"), headers={}, verb="GET")
    assert captured["timeout"] == (5, 30)
    assert captured["verify"] is True


def test_call_rest_verify_can_be_overridden(monkeypatch):
    captured = {}
    def fake_request(verb, url, **kwargs):
        captured.update(kwargs)
        return MagicMock(status_code=200)
    monkeypatch.setattr("AlfacoLib.atlassian_client.requests.request", fake_request)
    call_rest("u", body=None, auth=("a", "b"), headers={}, verb="GET", verify=False)
    assert captured["verify"] is False


def test_list_projects_returns_key_name_pairs():
    with requests_mock.Mocker() as m:
        m.get(
            "https://acme.atlassian.net/rest/api/3/project/",
            json=[{"key": "BUS", "name": "Business"}, {"key": "DEV", "name": "Dev"}],
        )
        result = list_projects(
            "https://acme.atlassian.net/rest/api/3/project/",
            auth=("alice", "tok"),
            headers={"Accept": "application/json"},
        )
    assert result == ["BUS-Business", "DEV-Dev"]


def test_list_projects_raises_on_http_error():
    with requests_mock.Mocker() as m:
        m.get("https://acme.atlassian.net/rest/api/3/project/", status_code=401, text="unauth")
        try:
            list_projects(
                "https://acme.atlassian.net/rest/api/3/project/",
                auth=("alice", "tok"),
                headers={},
            )
        except RuntimeError as e:
            assert "401" in str(e)
        else:
            assert False, "RuntimeError attendue"
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `python -m pytest plugins/AlfacoLib/tests/test_atlassian_client.py -v`
Expected: tous FAIL (`call_rest` n'existe pas).

- [ ] **Step 3: Implémenter `plugins/AlfacoLib/atlassian_client.py`**

```python
# -*- coding: utf-8 -*-
"""Wrapper REST minimal pour les API Atlassian.

Substitut moderne de modules/tools.py :
- verify TLS configurable (défaut True)
- timeout configurable (défaut connect=5s, read=30s)
- exceptions remontées au lieu d'être masquées
"""
from __future__ import annotations

import requests


DEFAULT_TIMEOUT = (5, 30)


def call_rest(url, body, auth, headers, verb="GET", verify=True, timeout=DEFAULT_TIMEOUT):
    """Effectue une requête HTTP authentifiée et retourne la `requests.Response`.

    Aucun parsing : l'appelant décide quoi faire de la réponse.
    """
    return requests.request(
        verb,
        url,
        headers=headers,
        auth=auth,
        data=body,
        verify=verify,
        timeout=timeout,
    )


def list_projects(url, auth, headers, verify=True, timeout=DEFAULT_TIMEOUT):
    """Récupère la liste des projets Jira sous la forme ['KEY-Nom', ...].

    Raise:
        RuntimeError si le serveur ne répond pas 200.
    """
    response = requests.get(url, auth=auth, headers=headers, verify=verify, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"GET {url} → {response.status_code} : {response.text[:200]}"
        )
    return [f"{p['key']}-{p['name']}" for p in response.json()]
```

- [ ] **Step 4: Relancer les tests**

Run: `python -m pytest plugins/AlfacoLib/tests/test_atlassian_client.py -v`
Expected: 6 tests PASS. Si `requests-mock` manque : `pip install requests-mock`.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/atlassian_client.py plugins/AlfacoLib/tests/test_atlassian_client.py
git commit -m "AlfacoLib : client REST avec verify/timeout configurables et erreurs explicites"
```

---

### Task 9: `AlfacoLib` — `io.py` (TDD)

**Files:**
- Create: `plugins/AlfacoLib/io.py`
- Create: `plugins/AlfacoLib/tests/test_io.py`

- [ ] **Step 1: Écrire les tests**

Crée `plugins/AlfacoLib/tests/test_io.py` :

```python
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
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `python -m pytest plugins/AlfacoLib/tests/test_io.py -v`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implémenter `plugins/AlfacoLib/io.py`**

```python
# -*- coding: utf-8 -*-
"""Helpers IO sans dépendances Sublime.

Substitut moderne de modules/tools.py (saveFichier/readFichier) :
- encodage UTF-8 explicite
- création des dossiers parents
- chemins via pathlib (cross-platform, plus de '\\' codés en dur)
"""
from __future__ import annotations

from pathlib import Path


def save_file(content, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def read_file(path):
    return Path(path).read_text(encoding="utf-8")


def build_response_path(folder, timestamp):
    return Path(folder) / f"error_api_call_{timestamp}.html"


def build_payload_path(folder, jira_key):
    return Path(folder) / f"{jira_key}.json"
```

- [ ] **Step 4: Relancer les tests**

Run: `python -m pytest plugins/AlfacoLib/tests/test_io.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/io.py plugins/AlfacoLib/tests/test_io.py
git commit -m "AlfacoLib : helpers IO en UTF-8 avec pathlib"
```

---

### Task 10: `AlfacoLib` — `logger.py` (debug flag)

**Files:**
- Create: `plugins/AlfacoLib/logger.py`
- Create: `plugins/AlfacoLib/tests/test_logger.py`

- [ ] **Step 1: Écrire les tests**

Crée `plugins/AlfacoLib/tests/test_logger.py` :

```python
"""Tests du logger Alfaco."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.logger import get_logger  # noqa: E402


def test_logger_silent_when_debug_off(capsys):
    log = get_logger("X", debug=False)
    log.debug("hello")
    log.info("world")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_logger_prints_with_prefix_when_debug_on(capsys):
    log = get_logger("X", debug=True)
    log.debug("hello")
    captured = capsys.readouterr()
    assert "[Alfaco][X] hello" in captured.out


def test_logger_warn_always_prints(capsys):
    log = get_logger("X", debug=False)
    log.warn("oops")
    captured = capsys.readouterr()
    assert "[Alfaco][X][WARN] oops" in captured.out
```

- [ ] **Step 2: Implémenter `plugins/AlfacoLib/logger.py`**

```python
# -*- coding: utf-8 -*-
"""Logger minimal pour les plugins Alfaco.

Remplace les print() bruts disséminés dans le code legacy.
"""
from __future__ import annotations


class _Logger:
    def __init__(self, name, debug):
        self._name = name
        self._debug = debug

    def debug(self, msg):
        if self._debug:
            print(f"[Alfaco][{self._name}] {msg}")

    info = debug

    def warn(self, msg):
        print(f"[Alfaco][{self._name}][WARN] {msg}")


def get_logger(name, debug=False):
    return _Logger(name, bool(debug))
```

- [ ] **Step 3: Lancer les tests**

Run: `python -m pytest plugins/AlfacoLib/tests/test_logger.py -v`
Expected: 3 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoLib/logger.py plugins/AlfacoLib/tests/test_logger.py
git commit -m "AlfacoLib : logger avec flag debug"
```

---

### Task 11: `AlfacoLib` — métadonnées du package

**Files:**
- Create: `plugins/AlfacoLib/.python-version`
- Create: `plugins/AlfacoLib/package-metadata.json`
- Create: `plugins/AlfacoLib/README.md`

- [ ] **Step 1: Créer `.python-version`**

```bash
echo "3.8" > plugins/AlfacoLib/.python-version
```

- [ ] **Step 2: Créer `package-metadata.json`**

```json
{
    "name": "AlfacoLib",
    "version": "0.1.0",
    "description": "Bibliothèque partagée des plugins Sublime Text Alfaco (Configuration, client REST Atlassian, IO)",
    "sublime_text": ">=4000",
    "platforms": ["*"],
    "dependencies": []
}
```

- [ ] **Step 3: Créer `README.md`**

```markdown
# AlfacoLib

Bibliothèque partagée des plugins Sublime Text Alfaco. Ne contient aucune commande utilisateur.

## Modules

- `config.Configuration` — Configuration empilée (settings + runtime).
- `atlassian_client.call_rest` / `list_projects` — Wrapper REST Atlassian (verify/timeout configurables).
- `io.save_file` / `read_file` / `build_response_path` / `build_payload_path` — IO UTF-8 cross-platform.
- `logger.get_logger` — Logger minimal avec flag debug.

## Installation

Depuis le monorepo : `make link PLUGIN=AlfacoLib`.

## Documentation

Voir `docs/plugins/alfaco-lib.md`.
```

- [ ] **Step 4: Lancer toute la suite de tests pour vérifier l'état global**

Run: `make test`
Expected: tous les tests des Tasks 3-10 passent (~24 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/.python-version plugins/AlfacoLib/package-metadata.json plugins/AlfacoLib/README.md
git commit -m "AlfacoLib : métadonnées du package (version 0.1.0)"
```

---

## Phase B — Migration des plugins

### Task 12: `AlfacoEditing` — scaffold

**Files:**
- Create: `plugins/AlfacoEditing/plugin.py`
- Create: `plugins/AlfacoEditing/commands/__init__.py`
- Create: `plugins/AlfacoEditing/tests/__init__.py`
- Create: `plugins/AlfacoEditing/tests/conftest.py`
- Create: `plugins/AlfacoEditing/.python-version`
- Create: `plugins/AlfacoEditing/package-metadata.json`
- Create: `plugins/AlfacoEditing/README.md`
- Create: `plugins/AlfacoEditing/alfaco-editing.sublime-settings`

- [ ] **Step 1: Scaffold via le générateur**

```bash
python tools/new_plugin.py Editing
```

- [ ] **Step 2: Créer le dossier tests**

```bash
mkdir -p plugins/AlfacoEditing/tests
touch plugins/AlfacoEditing/tests/__init__.py plugins/AlfacoEditing/tests/conftest.py
```

- [ ] **Step 3: Créer le fichier de settings**

`plugins/AlfacoEditing/alfaco-editing.sublime-settings` :

```json
{
    "alfaco_delimiter": "##"
}
```

- [ ] **Step 4: Vérifier que `plugin.py` rendu par le template est correct**

Lire `plugins/AlfacoEditing/plugin.py` — confirmer qu'il référence `alfaco-editing.sublime-settings`. Sinon corriger.

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoEditing/
git commit -m "AlfacoEditing : scaffold du plugin"
```

---

### Task 13: `AlfacoEditing` — commande `text_to_table`

**Files:**
- Create: `plugins/AlfacoEditing/commands/text_to_table.py`
- Modify: `plugins/AlfacoEditing/plugin.py` (ajout import)

- [ ] **Step 1: Créer la commande**

`plugins/AlfacoEditing/commands/text_to_table.py` :

```python
# -*- coding: utf-8 -*-
"""Commande text_to_table : duplique la sélection (lignes non-vides) en fin de fichier."""
import sublime_plugin


class TextToTableCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selection = self.view.sel()[0]
        selected_text = self.view.substr(selection)
        lines = [line for line in selected_text.split("\n") if line.strip()]
        self.view.insert(edit, self.view.size(), "\n" + "\n".join(lines))
```

- [ ] **Step 2: Modifier `plugins/AlfacoEditing/plugin.py` pour importer la classe**

À la fin du fichier, après `plugin_loaded()`, ajouter :

```python
from AlfacoEditing.commands.text_to_table import TextToTableCommand  # noqa: F401
```

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoEditing/commands/text_to_table.py plugins/AlfacoEditing/plugin.py
git commit -m "AlfacoEditing : commande text_to_table"
```

---

### Task 14: `AlfacoEditing` — commandes marqueurs (insert_tag, remove_tag, select_between_markers)

**Files:**
- Create: `plugins/AlfacoEditing/commands/insert_tag.py`
- Create: `plugins/AlfacoEditing/commands/remove_tag.py`
- Create: `plugins/AlfacoEditing/commands/select_between_markers.py`
- Modify: `plugins/AlfacoEditing/plugin.py`

- [ ] **Step 1: Créer `insert_tag.py`**

`plugins/AlfacoEditing/commands/insert_tag.py` :

```python
# -*- coding: utf-8 -*-
"""Insère un tag arbitraire à la position du curseur."""
import sublime_plugin


class InsertTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        pos = self.view.sel()[0].begin()
        self.view.insert(edit, pos, text)
```

- [ ] **Step 2: Créer `remove_tag.py`**

`plugins/AlfacoEditing/commands/remove_tag.py` :

```python
# -*- coding: utf-8 -*-
"""Supprime toutes les occurrences des tags listés (séparés par des virgules)."""
import sublime_plugin


class RemoveTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        tags = text.split(",")
        for tag in tags:
            for region in reversed(self.view.find_all(tag)):
                self.view.erase(edit, region)
```

- [ ] **Step 3: Créer `select_between_markers.py`**

`plugins/AlfacoEditing/commands/select_between_markers.py` :

```python
# -*- coding: utf-8 -*-
"""Sélectionne le texte entre <start> et <end>, l'ajoute en fin de fichier."""
import sublime
import sublime_plugin


class SelectBetweenMarkersCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        start = self.view.find("<start>", 0)
        end = self.view.find("<end>", 0)
        region = sublime.Region(start.end(), end.begin())
        self.view.sel().clear()
        self.view.sel().add(region)
        selected_text = self.view.substr(region)
        self.view.insert(edit, self.view.size(), "\n" + selected_text)
```

- [ ] **Step 4: Mettre à jour `plugin.py`**

Ajouter à la fin :

```python
from AlfacoEditing.commands.insert_tag import InsertTagCommand  # noqa: F401
from AlfacoEditing.commands.remove_tag import RemoveTagCommand  # noqa: F401
from AlfacoEditing.commands.select_between_markers import SelectBetweenMarkersCommand  # noqa: F401
```

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoEditing/commands/insert_tag.py plugins/AlfacoEditing/commands/remove_tag.py plugins/AlfacoEditing/commands/select_between_markers.py plugins/AlfacoEditing/plugin.py
git commit -m "AlfacoEditing : commandes de gestion des marqueurs"
```

---

### Task 15: `AlfacoEditing` — `date_selection`, `show_file_name`, `modify_setting_from_selection`

**Files:**
- Create: `plugins/AlfacoEditing/commands/date_selection.py`
- Create: `plugins/AlfacoEditing/commands/show_file_name.py`
- Create: `plugins/AlfacoEditing/commands/modify_setting_from_selection.py`
- Modify: `plugins/AlfacoEditing/plugin.py`

- [ ] **Step 1: Créer `date_selection.py`**

`plugins/AlfacoEditing/commands/date_selection.py` :

```python
# -*- coding: utf-8 -*-
"""Calcule date+N (N lu dans la sélection), ouvre un nouveau buffer avec le résultat."""
from datetime import datetime, timedelta

import sublime_plugin


class DateSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        num_days = int(self.view.substr(self.view.sel()[0]))
        future = (datetime.now() + timedelta(days=num_days)).strftime("%Y-%m-%d")
        output = f"##dt: {future} "
        new_view = self.view.window().new_file()
        new_view.run_command("insert", {"characters": output})
```

- [ ] **Step 2: Créer `show_file_name.py`** (renommé depuis `DonneNomFichierCommand`)

`plugins/AlfacoEditing/commands/show_file_name.py` :

```python
# -*- coding: utf-8 -*-
"""Affiche le chemin du fichier ouvert dans la console."""
import sublime
import sublime_plugin


class ShowFileNameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        active_view = sublime.active_window().active_view()
        file_name = active_view.file_name()
        if file_name:
            print(f"Le fichier ouvert dans la vue actuelle est : {file_name}")
        else:
            print("Aucun fichier ouvert dans la vue actuelle")
```

- [ ] **Step 3: Créer `modify_setting_from_selection.py`**

`plugins/AlfacoEditing/commands/modify_setting_from_selection.py` :

```python
# -*- coding: utf-8 -*-
"""Stocke la sélection comme alfaco_delimiter et l'insère à la position du curseur."""
import sublime
import sublime_plugin


class ModifySettingFromSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selected_text = self.view.substr(self.view.sel()[0])
        settings = sublime.load_settings("alfaco-editing.sublime-settings")
        settings.set("alfaco_delimiter", selected_text)
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), settings.get("alfaco_delimiter"))
```

- [ ] **Step 4: Mettre à jour `plugin.py`**

```python
from AlfacoEditing.commands.date_selection import DateSelectionCommand  # noqa: F401
from AlfacoEditing.commands.show_file_name import ShowFileNameCommand  # noqa: F401
from AlfacoEditing.commands.modify_setting_from_selection import ModifySettingFromSelectionCommand  # noqa: F401
```

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoEditing/commands/date_selection.py plugins/AlfacoEditing/commands/show_file_name.py plugins/AlfacoEditing/commands/modify_setting_from_selection.py plugins/AlfacoEditing/plugin.py
git commit -m "AlfacoEditing : commandes date_selection, show_file_name, modify_setting_from_selection"
```

---

### Task 16: `AlfacoEditing` — `show_selected_input` (avec correction du bug `nput_view`)

**Files:**
- Create: `plugins/AlfacoEditing/commands/show_selected_input.py`
- Modify: `plugins/AlfacoEditing/plugin.py`

- [ ] **Step 1: Créer la commande corrigée**

`plugins/AlfacoEditing/commands/show_selected_input.py` :

```python
# -*- coding: utf-8 -*-
"""Ouvre une input panel (correction du bug nput_view du legacy)."""
import sublime
import sublime_plugin


class ShowSelectedInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        input_view = self.window.show_input_panel(
            caption="Example",
            initial_text="Example",
            on_done=None,
            on_change=None,
            on_cancel=None,
        )
        input_view.add_regions(
            "example",
            [sublime.Region(0, 7)],
            scope="region.redish",
            flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SQUIGGLY_UNDERLINE,
        )
```

- [ ] **Step 2: Mettre à jour `plugin.py`**

```python
from AlfacoEditing.commands.show_selected_input import ShowSelectedInputCommand  # noqa: F401
```

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoEditing/commands/show_selected_input.py plugins/AlfacoEditing/plugin.py
git commit -m "AlfacoEditing : show_selected_input avec correction du bug nput_view"
```

---

### Task 17: `AlfacoEditing` — ressources (snippets, macros, keymaps, palette)

**Files:**
- Create: `plugins/AlfacoEditing/snippets/alfaco-key.sublime-snippet`
- Create: `plugins/AlfacoEditing/macros/replace.sublime-macro`
- Create: `plugins/AlfacoEditing/Default (Linux).sublime-keymap`
- Create: `plugins/AlfacoEditing/Default (Windows).sublime-keymap`
- Create: `plugins/AlfacoEditing/Default (OSX).sublime-keymap`
- Create: `plugins/AlfacoEditing/Default.sublime-commands`

- [ ] **Step 1: Copier le snippet et la macro**

```bash
mkdir -p plugins/AlfacoEditing/snippets plugins/AlfacoEditing/macros
cp snippets/alfaco-key.sublime-snippet plugins/AlfacoEditing/snippets/
cp macros/replace.sublime-macro plugins/AlfacoEditing/macros/
```

- [ ] **Step 2: Créer `Default (Linux).sublime-keymap`**

```json
[
    { "keys": ["ctrl+alt+t"], "command": "text_to_table", "context": [{ "key": "selection_empty", "operator": "equal", "operand": false }] },
    { "keys": ["ctrl+alt+s+b"], "command": "select_between_markers" },
    { "keys": ["ctrl+alt+t+s"], "command": "insert_tag", "args": { "text": "<start>" } },
    { "keys": ["ctrl+alt+t+e"], "command": "insert_tag", "args": { "text": "<end>" } },
    { "keys": ["ctrl+alt+d"], "command": "remove_tag", "args": { "text": "<end>,<start>" } }
]
```

- [ ] **Step 3: Créer `Default (Windows).sublime-keymap`**

```json
[
    { "keys": ["ctrl+alt+t"], "command": "text_to_table", "context": [{ "key": "selection_empty", "operator": "equal", "operand": false }] },
    { "keys": ["ctrl+alt+s+b"], "command": "select_between_markers" },
    { "keys": ["ctrl+alt+t+s"], "command": "insert_tag", "args": { "text": "<start>" } },
    { "keys": ["ctrl+alt+t+e"], "command": "insert_tag", "args": { "text": "<end>" } },
    { "keys": ["ctrl+alt+d"], "command": "remove_tag", "args": { "text": "<end>,<start>" } },
    { "keys": ["ctrl+alt+a"], "command": "date_selection" },
    { "keys": ["ctrl+alt+m"], "command": "modify_setting_from_selection" }
]
```

- [ ] **Step 4: Créer `Default (OSX).sublime-keymap`**

```json
[
    { "keys": ["ctrl+super+t"], "command": "text_to_table", "context": [{ "key": "selection_empty", "operator": "equal", "operand": false }] },
    { "keys": ["ctrl+super+s+b"], "command": "select_between_markers" },
    { "keys": ["ctrl+super+t+s"], "command": "insert_tag", "args": { "text": "<start>" } },
    { "keys": ["ctrl+super+t+e"], "command": "insert_tag", "args": { "text": "<end>" } },
    { "keys": ["ctrl+super+d"], "command": "remove_tag", "args": { "text": "<end>,<start>" } }
]
```

- [ ] **Step 5: Créer `Default.sublime-commands` (palette)**

```json
[
    { "caption": "AlfacoEditing: text to table", "command": "text_to_table" },
    { "caption": "AlfacoEditing: show file name", "command": "show_file_name" },
    { "caption": "AlfacoEditing: select between markers", "command": "select_between_markers" }
]
```

- [ ] **Step 6: Commit**

```bash
git add plugins/AlfacoEditing/snippets/ plugins/AlfacoEditing/macros/ "plugins/AlfacoEditing/Default (Linux).sublime-keymap" "plugins/AlfacoEditing/Default (Windows).sublime-keymap" "plugins/AlfacoEditing/Default (OSX).sublime-keymap" plugins/AlfacoEditing/Default.sublime-commands
git commit -m "AlfacoEditing : snippets, macros, keymaps et palette"
```

---

### Task 18: `AlfacoEditing` — validation manuelle dans Sublime

- [ ] **Step 1: Désactiver temporairement le legacy pour éviter les conflits**

```bash
mv AlfacoPlugins.py AlfacoPlugins.py.disabled
mv text_to_table.py text_to_table.py.disabled
```

> Note : ce désactivage est local (jamais commité). Sera annulé après la validation par `mv …disabled …` (Step 6).

- [ ] **Step 2: Linker AlfacoLib + AlfacoEditing**

```bash
make link PLUGIN=AlfacoLib
make link PLUGIN=AlfacoEditing
```

- [ ] **Step 3: Redémarrer Sublime Text**

Action manuelle. Vérifier la console (`` Ctrl+` ``) : aucune exception ; pas de `[Alfaco]` warning.

- [ ] **Step 4: Tester chaque commande**

Dans un buffer scratch, vérifier :
1. Sélectionner 3 lignes non-vides → `Ctrl+Alt+T` → les lignes sont dupliquées en fin de fichier.
2. `Ctrl+Alt+T+S` puis `Ctrl+Alt+T+E` à deux endroits → `<start>` et `<end>` s'insèrent.
3. `Ctrl+Alt+S+B` → la sélection entre marqueurs s'ajoute en fin.
4. `Ctrl+Alt+D` → les marqueurs sont supprimés.
5. (Windows uniquement) Sélectionner `7` → `Ctrl+Alt+A` → un nouveau buffer s'ouvre avec `##dt: <date+7> `.
6. Palette → `AlfacoEditing: show file name` → la console affiche le chemin du fichier courant.

- [ ] **Step 5: Vérifier l'absence de bug `nput_view`**

Palette → invoquer `Show Selected Input` (s'il est dans la palette ; sinon via la console : `view.window().run_command("show_selected_input")`). Aucune exception attendue.

- [ ] **Step 6: Réactiver le legacy**

```bash
mv AlfacoPlugins.py.disabled AlfacoPlugins.py
mv text_to_table.py.disabled text_to_table.py
```

- [ ] **Step 7: Pas de commit (validation manuelle, aucun fichier modifié)**

Si des bugs sont trouvés : corriger dans la branche, commiter (« correction de bug détecté en validation AlfacoEditing »), réessayer.

---

### Task 19: `AlfacoCompletion`

**Files:**
- Create: `plugins/AlfacoCompletion/plugin.py`
- Create: `plugins/AlfacoCompletion/.python-version`
- Create: `plugins/AlfacoCompletion/package-metadata.json`
- Create: `plugins/AlfacoCompletion/README.md`
- Create: `plugins/AlfacoCompletion/tests/__init__.py`

- [ ] **Step 1: Scaffold**

```bash
python tools/new_plugin.py Completion
mkdir -p plugins/AlfacoCompletion/tests
touch plugins/AlfacoCompletion/tests/__init__.py
```

- [ ] **Step 2: Remplacer `plugin.py` par le contenu réel**

Réécrire entièrement `plugins/AlfacoCompletion/plugin.py` :

```python
# -*- coding: utf-8 -*-
"""Auto-complétion statique pour les buffers Python."""
import sublime_plugin


class AlfacoCompletion(sublime_plugin.EventListener):
    AVAILABLE = ["def", "class", "None", "True", "False"]

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.python"):
            return []
        prefix = prefix.lower()
        return [c for c in self.AVAILABLE if c.lower().startswith(prefix)]
```

- [ ] **Step 3: Validation manuelle**

```bash
mv AlfacoCompletion.py AlfacoCompletion.py.disabled
make link PLUGIN=AlfacoCompletion
```

Redémarrer Sublime, ouvrir un fichier `.py`, taper `def` lentement → l'auto-complétion propose `def`. Pas d'exception.

- [ ] **Step 4: Réactiver le legacy**

```bash
mv AlfacoCompletion.py.disabled AlfacoCompletion.py
```

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoCompletion/
git commit -m "AlfacoCompletion : migration vers la nouvelle structure"
```

---

### Task 20: `AlfacoAtlassian` — scaffold + plugin.py

**Files:**
- Create: `plugins/AlfacoAtlassian/plugin.py`
- Create: `plugins/AlfacoAtlassian/commands/__init__.py`
- Create: `plugins/AlfacoAtlassian/tests/__init__.py`
- Create: `plugins/AlfacoAtlassian/.python-version`
- Create: `plugins/AlfacoAtlassian/package-metadata.json`
- Create: `plugins/AlfacoAtlassian/README.md`
- Create: `plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings`

- [ ] **Step 1: Scaffold**

```bash
python tools/new_plugin.py Atlassian
mkdir -p plugins/AlfacoAtlassian/tests
touch plugins/AlfacoAtlassian/tests/__init__.py
```

- [ ] **Step 2: Créer `alfaco-atlassian.sublime-settings`** (fusionne les deux settings legacy + ajoute clés manquantes)

```json
{
    "api_rest_version": "3",
    "tls_verify": true,
    "path_json_files_folder": "",
    "jira_login": "",
    "jira_password": "",
    "default_organisation": "",
    "atlassian": {
        "organisations": {
            "business projects": { "url_key": "business-projects", "jira": true, "confluence": true }
        }
    }
}
```

> **Note** : les valeurs sont vides — l'utilisateur doit les remplir dans `User/alfaco-atlassian.sublime-settings`. Plus de catalogue d'organisations privées committé.

- [ ] **Step 3: Réécrire `plugin.py`** avec import des modules de lib + boilerplate `importlib.reload`

`plugins/AlfacoAtlassian/plugin.py` :

```python
# -*- coding: utf-8 -*-
"""Entry point du plugin AlfacoAtlassian."""
import importlib

from AlfacoLib import config as _alfacolib_config
from AlfacoLib import atlassian_client as _alfacolib_client
from AlfacoLib import io as _alfacolib_io
from AlfacoLib import logger as _alfacolib_logger

_LIB_MODULES = (_alfacolib_config, _alfacolib_client, _alfacolib_io, _alfacolib_logger)

config = None
log = None


def plugin_loaded():
    global config, log
    for mod in _LIB_MODULES:
        importlib.reload(mod)
    config = _alfacolib_config.Configuration([
        "alfaco-atlassian.sublime-settings",
        "Preferences.sublime-settings",
    ])
    log = _alfacolib_logger.get_logger("Atlassian", debug=config.get("debug", False))
```

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoAtlassian/
git commit -m "AlfacoAtlassian : scaffold + plugin_loaded avec importlib.reload"
```

---

### Task 21: `AlfacoAtlassian` — `select_organisation` et `select_jira_project`

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/select_organisation.py`
- Create: `plugins/AlfacoAtlassian/commands/select_jira_project.py`
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1: Créer `select_organisation.py`** (renommé depuis `GetListOrganisationCommand`)

```python
# -*- coding: utf-8 -*-
"""Affiche les organisations Atlassian configurées et stocke le choix dans la config runtime."""
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class SelectOrganisationCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        atlassian = _atlassian_plugin.config.get("atlassian", {})
        orgs = atlassian.get("organisations", {})
        self._labels = list(orgs.keys())
        self._orgs = orgs
        self.view.show_popup_menu(self._labels, self._on_done)

    def _on_done(self, index):
        if index == -1:
            return
        url_key = self._orgs[self._labels[index]]["url_key"]
        _atlassian_plugin.config.set("default_organisation", url_key)
        _atlassian_plugin.log.info(f"organisation sélectionnée : {url_key}")
```

- [ ] **Step 2: Créer `select_jira_project.py`** (renommé depuis `GetJiraListForOrganisationCommand`)

```python
# -*- coding: utf-8 -*-
"""GET /project/, popup KEY-Nom, stocke project_key."""
import re

import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import list_projects


class SelectJiraProjectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        try:
            self._items = list_projects(
                cfg.base_url() + "project/",
                auth=cfg.jira_auth(),
                headers=cfg.get("headers", {"Accept": "application/json"}),
                verify=cfg.get("tls_verify", True),
            )
        except RuntimeError as e:
            _atlassian_plugin.log.warn(str(e))
            return
        self.view.show_popup_menu(self._items, self._on_done)

    def _on_done(self, index):
        if index == -1:
            return
        match = re.match(r"^\w+", self._items[index])
        if match:
            _atlassian_plugin.config.set("project_key", match.group())
            _atlassian_plugin.log.info(f"project_key : {match.group()}")
```

- [ ] **Step 3: Mettre à jour `plugin.py`**

```python
from AlfacoAtlassian.commands.select_organisation import SelectOrganisationCommand  # noqa: F401
from AlfacoAtlassian.commands.select_jira_project import SelectJiraProjectCommand  # noqa: F401
```

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/select_organisation.py plugins/AlfacoAtlassian/commands/select_jira_project.py plugins/AlfacoAtlassian/plugin.py
git commit -m "AlfacoAtlassian : commandes select_organisation et select_jira_project (renommées)"
```

---

### Task 22: `AlfacoAtlassian` — `create_jira_issue` (avec corrections de bugs)

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/create_jira_issue.py`
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1: Créer la commande corrigée**

`plugins/AlfacoAtlassian/commands/create_jira_issue.py` :

```python
# -*- coding: utf-8 -*-
"""POST le buffer JSON vers Jira, sauvegarde la réponse et le payload.

Migration de AppelRestApiCommand avec les corrections suivantes :
- Plus de "\\\\" : usage de pathlib.Path (build_response_path / build_payload_path).
- verify TLS et timeout configurables (via Configuration).
- Headers conservés (plus écrasés en cours de route).
- Erreurs HTTP remontées sans masquage.
"""
import json
import time

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest
from AlfacoLib.io import save_file, build_response_path, build_payload_path


class CreateJiraIssueCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config
        contenu = self.view.substr(sublime.Region(0, self.view.size()))

        url = cfg.base_url() + "issue/"
        headers = cfg.get("headers", {"Content-type": "application/json", "Accept": "application/json"})
        response = call_rest(
            url,
            body=contenu,
            auth=cfg.jira_auth(),
            headers=headers,
            verb="POST",
            verify=cfg.get("tls_verify", True),
        )

        new_view = self.view.window().new_file()
        new_view.run_command("insert", {"characters": response.text})

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            try:
                jira_key = response.json()["key"]
                save_file(contenu, build_payload_path(folder, jira_key))
            except (KeyError, ValueError):
                _atlassian_plugin.log.warn("Réponse sans 'key' — payload non sauvegardé.")
```

- [ ] **Step 2: Mettre à jour `plugin.py`**

```python
from AlfacoAtlassian.commands.create_jira_issue import CreateJiraIssueCommand  # noqa: F401
```

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/create_jira_issue.py plugins/AlfacoAtlassian/plugin.py
git commit -m "AlfacoAtlassian : create_jira_issue (renommée) avec correctifs (pathlib, verify, timeout)"
```

---

### Task 23: `AlfacoAtlassian` — `open_jira_projects`, `init_json_jira`, `set_jira_project_in_snippet`

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/open_jira_projects.py`
- Create: `plugins/AlfacoAtlassian/commands/init_json_jira.py`
- Create: `plugins/AlfacoAtlassian/commands/set_jira_project_in_snippet.py`
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1: Créer `open_jira_projects.py`** (sans le `print(jira_password)`)

```python
# -*- coding: utf-8 -*-
"""Affiche le login Jira en console (sans le password — bug du legacy corrigé)."""
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class OpenJiraProjectsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        login, _password = _atlassian_plugin.config.jira_auth()
        _atlassian_plugin.log.info(f"jira_login = {login}")
        _atlassian_plugin.log.info("jira_password : (masqué)")
```

- [ ] **Step 2: Créer `init_json_jira.py`**

```python
# -*- coding: utf-8 -*-
"""Ouvre un buffer scratch et y insère le snippet jira pré-rempli."""
from datetime import datetime, timedelta

import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin


class InitJsonJiraCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        current_line = self.view.substr(self.view.line(self.view.sel()[0]))
        new_view = self.view.window().new_file()
        new_view.set_name("Init new Jira")
        new_view.set_scratch(True)
        args["duedate"] = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        args["selection"] = current_line.strip()
        args["jira_key"] = _atlassian_plugin.config.get("project_key", "")
        new_view.run_command("insert_snippet", args)
```

- [ ] **Step 3: Créer `set_jira_project_in_snippet.py`**

```python
# -*- coding: utf-8 -*-
"""Remplace "key": "" par "key": "<args.text>" dans le buffer."""
import re

import sublime
import sublime_plugin


class SetJiraProjectInSnippetCommand(sublime_plugin.TextCommand):
    def run(self, edit, args):
        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)
        pattern = r'"key"\s*:\s*(""|\'\')'
        content = re.sub(pattern, f'"key": "{args["text"]}"', content)
        self.view.replace(edit, region, content)
```

- [ ] **Step 4: Mettre à jour `plugin.py`**

```python
from AlfacoAtlassian.commands.open_jira_projects import OpenJiraProjectsCommand  # noqa: F401
from AlfacoAtlassian.commands.init_json_jira import InitJsonJiraCommand  # noqa: F401
from AlfacoAtlassian.commands.set_jira_project_in_snippet import SetJiraProjectInSnippetCommand  # noqa: F401
```

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/open_jira_projects.py plugins/AlfacoAtlassian/commands/init_json_jira.py plugins/AlfacoAtlassian/commands/set_jira_project_in_snippet.py plugins/AlfacoAtlassian/plugin.py
git commit -m "AlfacoAtlassian : open_jira_projects (sans print du password), init_json_jira, set_jira_project_in_snippet"
```

---

### Task 24: `AlfacoAtlassian` — snippets, macro, menus, sidebar, keymaps

**Files:**
- Create: `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet`
- Create: `plugins/AlfacoAtlassian/snippets/confluence/page.sublime-snippet`
- Create: `plugins/AlfacoAtlassian/snippets/confluence/childPage.sublime-snippet`
- Create: `plugins/AlfacoAtlassian/snippets/confluence/space.sublime-snippet`
- Create: `plugins/AlfacoAtlassian/macros/addjira.sublime-macro`
- Create: `plugins/AlfacoAtlassian/Main.sublime-menu`
- Create: `plugins/AlfacoAtlassian/Context.sublime-menu`
- Create: `plugins/AlfacoAtlassian/Side Bar.sublime-menu`
- Create: `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`
- Create: `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`
- Create: `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`

- [ ] **Step 1: Copier les snippets et la macro depuis le legacy**

```bash
mkdir -p plugins/AlfacoAtlassian/snippets/jira plugins/AlfacoAtlassian/snippets/confluence plugins/AlfacoAtlassian/macros
cp snippets/jira/jira.sublime-snippet plugins/AlfacoAtlassian/snippets/jira/
cp snippets/confluence/page.sublime-snippet plugins/AlfacoAtlassian/snippets/confluence/
cp snippets/confluence/childPage.sublime-snippet plugins/AlfacoAtlassian/snippets/confluence/
cp snippets/confluence/space.sublime-snippet plugins/AlfacoAtlassian/snippets/confluence/
cp macros/addjira.sublime-macro plugins/AlfacoAtlassian/macros/
```

> **Important** : on ne copie **pas** `snippets/jira.sublime-snippet`, `page.sublime-snippet`, `childPage.sublime-snippet`, `space.sublime-snippet` (doublons à la racine — supprimés en Phase C, voir Task 27).

- [ ] **Step 2: Mettre à jour la macro `addjira` pour pointer vers le snippet du nouveau package**

Lire `plugins/AlfacoAtlassian/macros/addjira.sublime-macro`. Si elle référence `Packages/User/jira.sublime-snippet`, remplacer par `Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet`.

- [ ] **Step 3: Créer `Main.sublime-menu`** (branche Atlassian)

```json
[
    {
        "id": "tools",
        "children": [
            {
                "caption": "Alfaco",
                "id": "alfaco",
                "children": [
                    {
                        "caption": "Atlassian",
                        "id": "alfaco-atlassian",
                        "children": [
                            { "caption": "Sélectionner organisation", "command": "select_organisation" },
                            { "caption": "Sélectionner projet Jira", "command": "select_jira_project" },
                            { "caption": "Créer ticket Jira", "command": "create_jira_issue" },
                            { "caption": "Initialiser JSON Jira", "command": "init_json_jira" },
                            { "caption": "Open Jira projects (debug)", "command": "open_jira_projects" }
                        ]
                    }
                ]
            }
        ]
    },
    {
        "id": "preferences",
        "children": [
            {
                "id": "package-settings",
                "children": [
                    {
                        "caption": "AlfacoAtlassian",
                        "id": "alfaco-atlassian",
                        "children": [
                            { "caption": "Settings – Default", "args": { "file": "${packages}/AlfacoAtlassian/alfaco-atlassian.sublime-settings" }, "command": "open_file" },
                            { "caption": "Settings – User", "args": { "file": "${packages}/User/alfaco-atlassian.sublime-settings" }, "command": "open_file" }
                        ]
                    }
                ]
            }
        ]
    }
]
```

- [ ] **Step 4: Créer `Context.sublime-menu`**

```json
[
    {
        "caption": "AlfacoAtlassian",
        "children": [
            { "caption": "format JSON", "command": "pretty_json" },
            { "caption": "créer ticket Jira", "command": "create_jira_issue" },
            { "caption": "sélectionner projet Jira", "command": "select_jira_project" },
            { "caption": "sélectionner organisation", "command": "select_organisation" }
        ]
    }
]
```

- [ ] **Step 5: Créer `Side Bar.sublime-menu`**

```json
[
    {
        "caption": "AlfacoAtlassian",
        "children": [
            { "caption": "format JSON", "command": "pretty_json" },
            { "caption": "open jira projects (debug)", "command": "open_jira_projects" }
        ]
    }
]
```

- [ ] **Step 6: Créer `Default (Linux).sublime-keymap`**

```json
[
    {
        "keys": ["ctrl+j"],
        "command": "insert_snippet",
        "args": { "name": "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet" }
    },
    {
        "keys": ["f2"],
        "command": "run_macro_file",
        "args": { "file": "Packages/AlfacoAtlassian/macros/addjira.sublime-macro" }
    }
]
```

- [ ] **Step 7: Créer `Default (Windows).sublime-keymap`**

```json
[
    { "keys": ["ctrl+alt+j"], "command": "pretty_json" },
    { "keys": ["ctrl+j+l"], "command": "select_jira_project" },
    {
        "keys": ["super+n"],
        "command": "init_json_jira",
        "args": {
            "name": "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet",
            "jira_key": "ALFA",
            "description": "a completer"
        }
    },
    {
        "keys": ["ctrl+alt+w"],
        "command": "insert_snippet",
        "args": { "contents": "{\"fields\":${0:$SELECTION}}" }
    },
    { "keys": ["alt+j"], "command": "create_jira_issue" }
]
```

- [ ] **Step 8: Créer `Default (OSX).sublime-keymap`** (vide — pas de bindings OSX dans le legacy pour Atlassian)

```json
[]
```

- [ ] **Step 9: Commit**

```bash
git add plugins/AlfacoAtlassian/snippets/ plugins/AlfacoAtlassian/macros/ plugins/AlfacoAtlassian/Main.sublime-menu plugins/AlfacoAtlassian/Context.sublime-menu "plugins/AlfacoAtlassian/Side Bar.sublime-menu" "plugins/AlfacoAtlassian/Default (Linux).sublime-keymap" "plugins/AlfacoAtlassian/Default (Windows).sublime-keymap" "plugins/AlfacoAtlassian/Default (OSX).sublime-keymap"
git commit -m "AlfacoAtlassian : snippets, macro, menus, sidebar et keymaps (renommage)"
```

---

### Task 25: Validation d'intégration globale

- [ ] **Step 1: Désactiver tout le legacy**

```bash
mv AlfacoPlugins.py AlfacoPlugins.py.disabled
mv text_to_table.py text_to_table.py.disabled
mv AlfacoCompletion.py AlfacoCompletion.py.disabled
```

- [ ] **Step 2: Désinstaller tout, puis tout re-linker**

```bash
make uninstall
make link
make status
```

Expected `make status` :
```
  AlfacoAtlassian          link  (ou copy si WSL)
  AlfacoCompletion         link
  AlfacoEditing            link
  AlfacoLib                link
```

- [ ] **Step 3: Redémarrer Sublime Text**

Vérifier la console : aucun `Traceback`. Les `plugin_loaded()` des 3 plugins consommateurs doivent s'exécuter sans erreur.

- [ ] **Step 4: Tests fumigène — workflow Jira complet**

Pré-requis : avoir un fichier `User/alfaco-atlassian.sublime-settings` avec `jira_login`, `jira_password`, `default_organisation`, `path_json_files_folder` valides.

1. Palette → `AlfacoAtlassian: Sélectionner organisation` → choisir une org → console : `[Alfaco][Atlassian] organisation sélectionnée : <url_key>`.
2. Palette → `AlfacoAtlassian: Sélectionner projet Jira` → liste `KEY-Nom` → choisir un projet → console : `[Alfaco][Atlassian] project_key : <KEY>`.
3. `Super+N` (Windows) ou palette → `Initialiser JSON Jira` → un buffer scratch s'ouvre, snippet pré-rempli avec la `project_key`.
4. Compléter le JSON. `Alt+J` (Windows) ou palette → `Créer ticket Jira` → un nouveau buffer affiche la réponse, et `<folder>/error_api_call_*.html` + `<folder>/<KEY>.json` sont créés.
5. **Vérifier** : aucun `print(password)` dans la console.

- [ ] **Step 5: Tests fumigène — Editing**

Reproduire les 6 scénarios de la Task 18.

- [ ] **Step 6: Tests fumigène — Completion**

Ouvrir un `.py`, vérifier que `def`, `class`, etc. sont proposés.

- [ ] **Step 7: Réactiver le legacy** (uniquement le temps de la Phase B)

```bash
mv AlfacoPlugins.py.disabled AlfacoPlugins.py
mv text_to_table.py.disabled text_to_table.py
mv AlfacoCompletion.py.disabled AlfacoCompletion.py
```

> Note : ces fichiers seront supprimés à la Task 27.

- [ ] **Step 8: Si bugs trouvés, commits ciblés sur la branche**

Si tout passe : pas de commit. Sinon : un commit par bug, message « correction : <bug> en validation d'intégration ».

---

## Phase C — Nettoyage

### Task 26: Suppression du legacy à la racine

**Files:**
- Delete: `AlfacoPlugins.py`, `AlfacoCompletion.py`, `text_to_table.py`, `modules/`, `macros/`, `snippets/`, `alfaco.sublime-settings`, `alfaco-atlassian.sublime-settings`, `Default (Linux).sublime-keymap`, `Default (Windows).sublime-keymap`, `Default (OSX).sublime-keymap`, `Main.sublime-menu`, `Context.sublime-menu`, `Side Bar.sublime-menu`, `Default.sublime-commands`, `package-metadata.json`

- [ ] **Step 1: Désinstaller le legacy de Sublime (s'il pointait sur le dossier racine via Package Control)**

Si l'utilisateur avait fait `ln -s <repo> Packages/Alfaco`, retirer ce lien :

```bash
python tools/deploy.py uninstall --packages-dir <chemin> 2>/dev/null || true
# Puis manuellement : rm Packages/Alfaco si lien
```

- [ ] **Step 2: Supprimer les fichiers Python legacy**

```bash
git rm AlfacoPlugins.py AlfacoCompletion.py text_to_table.py
git rm -r modules/
```

- [ ] **Step 3: Supprimer les ressources Sublime à la racine**

```bash
git rm -r macros/ snippets/
git rm alfaco.sublime-settings alfaco-atlassian.sublime-settings
git rm "Default (Linux).sublime-keymap" "Default (Windows).sublime-keymap" "Default (OSX).sublime-keymap"
git rm Main.sublime-menu Context.sublime-menu "Side Bar.sublime-menu" Default.sublime-commands
git rm package-metadata.json
```

- [ ] **Step 4: Vérifier l'état**

Run: `git status`
Expected : tous les fichiers ci-dessus listés dans `Changes to be committed: deleted`.

Run: `ls`
Expected : `CLAUDE.md  LICENSE  Makefile  README.md  conftest.py  docs  plugins  pyproject.toml  tools` + `.gitignore` (caché).

- [ ] **Step 5: Commit**

```bash
git commit -m "suppression du code legacy à la racine"
```

---

### Task 27: Mise à jour de la documentation

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/contributing.md`
- Modify: `docs/configuration.md`
- Modify: `docs/installation.md`
- Modify: `docs/usage.md`
- Modify: `docs/troubleshooting.md`
- Create: `docs/deployment.md`
- Create: `docs/plugins/alfaco-lib.md`
- Create: `docs/plugins/alfaco-atlassian.md`
- Create: `docs/plugins/alfaco-editing.md`
- Create: `docs/plugins/alfaco-completion.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Réécrire `docs/README.md`** (sommaire monorepo)

Remplacer entièrement le contenu :

```markdown
# Documentation Alfaco

Monorepo des plugins Sublime Text 4 Alfaco.

## Plugins

| Plugin | Description | Doc |
|---|---|---|
| `AlfacoLib` | Bibliothèque partagée (Configuration, client REST Atlassian, IO, logger) | [plugins/alfaco-lib.md](plugins/alfaco-lib.md) |
| `AlfacoAtlassian` | Pilotage Jira/Confluence depuis l'éditeur | [plugins/alfaco-atlassian.md](plugins/alfaco-atlassian.md) |
| `AlfacoEditing` | Utilitaires d'édition (text-to-table, marqueurs, dates, tags) | [plugins/alfaco-editing.md](plugins/alfaco-editing.md) |
| `AlfacoCompletion` | Auto-complétion Python | [plugins/alfaco-completion.md](plugins/alfaco-completion.md) |

## Documentation transversale

- [Installation](installation.md) — pré-requis, déploiement, première config.
- [Architecture](architecture.md) — topologie multi-plugins, flux d'import inter-package.
- [Configuration](configuration.md) — clés des `.sublime-settings`, sécurité du token.
- [Déploiement](deployment.md) — Makefile, multi-OS, WSL.
- [Contributing](contributing.md) — workflow, `make new-plugin`, conventions.
- [Troubleshooting](troubleshooting.md) — bugs connus, diagnostic Atlassian.
```

- [ ] **Step 2: Réécrire `docs/architecture.md`** avec la nouvelle topologie

Remplacer le contenu actuel (qui décrit le legacy) par la section « Architecture cible » du spec, adaptée :
- Schéma ASCII de la topologie (copier depuis le spec).
- Structure du dépôt (copier depuis le spec).
- Flux d'import inter-package (copier depuis le spec).
- 5 subtilités Sublime (copier depuis le spec).

- [ ] **Step 3: Mettre à jour `docs/contributing.md`** avec le workflow monorepo

Remplacer la section « Cycle de développement » et « Ajouter une nouvelle commande » par :
- `make new-plugin NAME=Foo` pour créer un plugin.
- Convention « une commande = un fichier » dans `commands/`.
- Boilerplate `importlib.reload()` dans `plugin.py`.
- Mettre à jour les 3 keymaps simultanément.
- Tests dans `plugins/<Plugin>/tests/`.

- [ ] **Step 4: Mettre à jour `docs/configuration.md`** pour refléter les fichiers settings éclatés

- `alfaco-atlassian.sublime-settings` n'est plus le catalogue, c'est le settings d'`AlfacoAtlassian`.
- Ajouter `tls_verify`, `debug`.
- Retirer `alfaco_delimiter` qui passe dans `alfaco-editing.sublime-settings`.

- [ ] **Step 5: Mettre à jour `docs/installation.md`**

- Remplacer « cloner dans Packages/Alfaco » par « cloner où vous voulez puis `make link` ».
- Ajouter section sur `requests` (dépendance non déclarée).
- Ajouter section WSL (force `install` au lieu de `link`).

- [ ] **Step 6: Mettre à jour `docs/usage.md`**

- Renommer les commandes (table « Commandes Jira/Atlassian » → nouveaux noms).
- Préciser que les keymaps sont éclatées par plugin.

- [ ] **Step 7: Mettre à jour `docs/troubleshooting.md`**

- Marquer comme **résolus** : `nput_view`, login codé en dur, `setSetting("organisation", …)`, `verify=False`, pas de timeout, `\\` codés, méthodes cassées de `Configuration`, `print(password)`, snippet `2022-02-23`.
- Ajouter section « Erreurs spécifiques au monorepo » (import cyclique, plugin host différent, WSL et symlinks).

- [ ] **Step 8: Créer `docs/deployment.md`**

```markdown
# Déploiement

## Cibles Makefile

| Cible | Effet |
|---|---|
| `make link` | Symlinks `plugins/*` → `<Packages>/`. Mode dev : modifications immédiates. |
| `make install` | Copie `plugins/*` → `<Packages>/`. Mode utilisateur. |
| `make uninstall` | Supprime `<Packages>/Alfaco*`. |
| `make relink` | uninstall + link. |
| `make status` | État de chaque plugin (link/copy/absent). |
| `make new-plugin NAME=X` | Scaffold `plugins/AlfacoX/`. |
| `make test` | pytest sur `plugins/*/tests/`. |
| `make clean` | Nettoyage `__pycache__`, `.pytest_cache`. |

Variable `PLUGIN=AlfacoEditing` pour cibler un plugin spécifique.

## Détection multi-OS du dossier Packages/

Voir `tools/deploy.py:detect_packages_dir`. Override possible :
- Variable d'environnement `SUBLIME_PACKAGES_DIR`.
- Flag CLI `--packages-dir`.

| OS / Contexte | Chemin |
|---|---|
| Linux ST4 | `~/.config/sublime-text/Packages/` |
| Linux ST3 | `~/.config/sublime-text-3/Packages/` |
| macOS | `~/Library/Application Support/Sublime Text/Packages/` |
| Windows | `%APPDATA%\Sublime Text\Packages\` |
| WSL → Sublime hôte Windows | `/mnt/c/Users/<user>/AppData/Roaming/Sublime Text/Packages/` |

## WSL

Sous WSL, `make link` détecte l'environnement et force la copie : NTFS ne suit pas les symlinks WSL.

## Windows natif

`os.symlink` est tenté en premier ; en cas d'échec (Developer Mode désactivé), fallback sur `mklink /J` (junction). Aucun privilège admin requis dans les deux cas.
```

- [ ] **Step 9: Créer `docs/plugins/alfaco-lib.md`**

```markdown
# AlfacoLib

Bibliothèque partagée. **Pas de commande utilisateur**.

## API publique

### `config.Configuration`

```python
cfg = Configuration(["alfaco-X.sublime-settings", "Preferences.sublime-settings"])
cfg.get(key, default=None)        # lookup runtime → settings layers → default
cfg.set(key, value)                # ne mute QUE le runtime (pas Preferences)
cfg.jira_auth()                    # → (login, password)
cfg.base_url(version=None)         # → 'https://<org>.atlassian.net/rest/api/<v>/'
```

### `atlassian_client`

```python
call_rest(url, body, auth, headers, verb="GET", verify=True, timeout=(5, 30))
list_projects(url, auth, headers, verify=True, timeout=(5, 30))
```

### `io`

```python
save_file(content, path)            # UTF-8, crée les dossiers parents
read_file(path)                     # UTF-8
build_response_path(folder, ts)     # → folder/error_api_call_<ts>.html
build_payload_path(folder, key)     # → folder/<key>.json
```

### `logger`

```python
log = get_logger("MonPlugin", debug=cfg.get("debug", False))
log.debug("trace")    # affiché si debug=True
log.info("info")      # idem
log.warn("oops")      # toujours affiché
```

## Pourquoi un package séparé ?

Voir [architecture.md](../architecture.md). Pattern utilisé par `Default`, `LSP`, `PackageControl`.
```

- [ ] **Step 10: Créer `docs/plugins/alfaco-atlassian.md`**

```markdown
# AlfacoAtlassian

Pilotage Jira/Confluence depuis Sublime Text.

## Commandes

| Commande Sublime | Effet |
|---|---|
| `select_organisation` | Choisit une organisation Atlassian dans la config runtime. |
| `select_jira_project` | `GET /project/`, popup, stocke la `project_key`. |
| `create_jira_issue` | POST le buffer JSON vers `…/issue/`, sauvegarde réponse + payload. |
| `init_json_jira` | Ouvre un buffer scratch + insère le snippet Jira pré-rempli. |
| `set_jira_project_in_snippet` | Remplace `"key": ""` par `"key": "<X>"`. |
| `open_jira_projects` | Affiche le login Jira en console (debug). |

## Configuration

Voir [../configuration.md](../configuration.md).

## Snippets

- `snippets/jira/jira.sublime-snippet` — payload Jira REST.
- `snippets/confluence/page.sublime-snippet` — page Confluence.
- `snippets/confluence/childPage.sublime-snippet` — page Confluence enfant.
- `snippets/confluence/space.sublime-snippet` — espace Confluence.

## Raccourcis

Voir [../usage.md](../usage.md#raccourcis-clavier).
```

- [ ] **Step 11: Créer `docs/plugins/alfaco-editing.md`**

```markdown
# AlfacoEditing

Utilitaires d'édition (sans dépendance Atlassian).

## Commandes

| Commande Sublime | Effet |
|---|---|
| `text_to_table` | Duplique la sélection (lignes non-vides) en fin de fichier. |
| `select_between_markers` | Sélectionne entre `<start>` et `<end>`, ajoute en fin de fichier. |
| `insert_tag` | Insère un tag arbitraire (arg `text`). |
| `remove_tag` | Supprime des tags listés (arg `text` séparé par `,`). |
| `date_selection` | Calcule date+N (N lu dans la sélection), ouvre buffer avec `##dt: <date>`. |
| `show_file_name` | Affiche le chemin du fichier ouvert en console. |
| `modify_setting_from_selection` | Stocke la sélection comme `alfaco_delimiter`. |
| `show_selected_input` | Ouvre une input panel (corrigé du bug `nput_view`). |
```

- [ ] **Step 12: Créer `docs/plugins/alfaco-completion.md`**

```markdown
# AlfacoCompletion

Auto-complétion statique (`def`, `class`, `None`, `True`, `False`) en scope `source.python`.

Squelette de démonstration plus qu'utilité réelle (Sublime fournit déjà ces complétions).
```

- [ ] **Step 13: Mettre à jour `CLAUDE.md`** racine

Remplacer la section « Architecture » et « Run model » pour refléter la structure monorepo. Pointer vers `docs/architecture.md` et `docs/deployment.md`.

- [ ] **Step 14: Commit**

```bash
git add docs/ CLAUDE.md
git commit -m "mise à jour de la documentation pour la structure multi-plugins"
```

---

### Task 28: Réécriture du `README.md` racine

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Remplacer entièrement le `README.md`**

```markdown
# Alfaco

Monorepo des plugins Sublime Text 4 Alfaco — pilotage Atlassian (Jira/Confluence) et utilitaires d'édition.

## Plugins

- **AlfacoLib** — bibliothèque partagée (Configuration, client REST Atlassian, IO, logger).
- **AlfacoAtlassian** — création d'issues Jira, sélection d'organisations/projets, snippets Confluence.
- **AlfacoEditing** — text-to-table, marqueurs `<start>`/`<end>`, insertion de date, gestion de tags.
- **AlfacoCompletion** — auto-complétion Python.

## Installation rapide

```bash
git clone https://github.com/jlbionville/Sublimetext.git
cd Sublimetext
make link              # mode dev (symlinks)
# OU
make install           # mode utilisateur (copie)
```

Puis créer `<Packages>/User/alfaco-atlassian.sublime-settings` avec votre token API Atlassian — voir [docs/configuration.md](docs/configuration.md).

## Documentation

- [Installation](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Déploiement](docs/deployment.md)
- [Contributing](docs/contributing.md)
- [Troubleshooting](docs/troubleshooting.md)

## Licence

Voir [LICENSE](LICENSE).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "réécriture du README racine pour le monorepo"
```

---

## Phase D — Finitions

### Task 29: CI GitHub Actions

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Créer le workflow**

```yaml
name: tests

on:
  push:
    branches: [main, development, "refactor/*"]
  pull_request:
    branches: [main, development]

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.8"
      - run: pip install -e '.[dev]'
      - run: make test
```

- [ ] **Step 2: Vérifier que le workflow YAML est valide**

Run (si `yamllint` dispo) : `yamllint .github/workflows/test.yml`
Expected : pas d'erreurs. Sinon, vérification manuelle de la syntaxe.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ajout d'une CI GitHub Actions pour les tests"
```

---

### Task 30: PR et tag

- [ ] **Step 1: Pousser la branche**

```bash
git push -u origin refactor/multi-plugins
```

- [ ] **Step 2: Créer la PR vers `development` via `gh`**

```bash
gh pr create --base development --title "Refactorisation : monorepo multi-plugins" --body "$(cat <<'EOF'
## Résumé

Transforme le package Sublime monolithique Alfaco en monorepo de 4 packages :
- **AlfacoLib** (lib partagée)
- **AlfacoAtlassian** (Jira/Confluence)
- **AlfacoEditing** (utilitaires d'édition)
- **AlfacoCompletion** (auto-complétion Python)

## Spec

Voir `docs/superpowers/specs/2026-05-08-multi-plugins-monorepo-design.md`.

## Test plan

- [ ] `make test` passe (CI verte).
- [ ] `make link` puis redémarrage Sublime : aucun Traceback en console.
- [ ] Workflow Jira complet validé manuellement (sélection org → projet → création issue).
- [ ] Commandes AlfacoEditing : tous les raccourcis répondent.
- [ ] Aucun `print(password)` en console.
- [ ] Bugs documentés en `docs/troubleshooting.md` marqués comme résolus.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Attendre la review et le merge**

Action manuelle. Pas de commit.

- [ ] **Step 4: Après merge, tagger le monorepo**

```bash
git checkout development
git pull --ff-only
git tag -a monorepo-v0.2.0 -m "Refactorisation monorepo multi-plugins"
git push origin monorepo-v0.2.0
```

---

## Validation finale (critères d'acceptation du spec)

- [ ] `make link` produit un état Sublime fonctionnel, identique au comportement legacy.
- [ ] `make uninstall` retire intégralement les packages.
- [ ] `make test` passe sur CI.
- [ ] `make new-plugin NAME=Demo` produit un plugin minimal qui charge sans erreur.
- [ ] Les 9 bugs listés dans le spec (section « Bugs corrigés pendant la migration ») sont fermés.
- [ ] `docs/` est à jour, sans référence au layout legacy.
- [ ] PR `refactor/multi-plugins` mergée sur `development`.
- [ ] Tag `monorepo-v0.2.0` créé.

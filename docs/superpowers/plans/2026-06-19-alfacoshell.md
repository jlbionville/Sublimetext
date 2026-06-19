# AlfacoShell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Intégrer l'ex-plugin `AwsRunner` dans la suite Alfaco sous le nom **AlfacoShell** : exécuter la sélection courante comme commande shell (multi-OS) et afficher le résultat dans un buffer scratch.

**Architecture:** Plugin Sublime Text 4 **autonome** (pas de dépendance `AlfacoLib`). Logique pure isolée dans `domain.py` (résolution de l'argv par plateforme, prettify JSON, formatage du buffer) — testable hors Sublime. L'adapter `commands/run_selection.py` fait l'I/O (subprocess async + buffer). La config (préfixe d'exécution par OS, timeout) vit dans `alfaco-shell.sublime-settings`.

**Tech Stack:** Python 3.8 (plugin host ST4), stdlib uniquement (`subprocess`, `json`), pytest hors-Sublime.

**Référence spec :** `docs/superpowers/specs/2026-06-19-alfacoshell-design.md`

**Branche :** `feat/alfaco-shell` (déjà créée, le spec y est commité).

---

## File Structure

| Fichier | Responsabilité |
|---|---|
| `plugins/AlfacoShell/.python-version` | force le host 3.8 |
| `plugins/AlfacoShell/constants.py` | identité du package, clés de settings, défauts (dont `DEFAULT_EXEC_BY_PLATFORM`) |
| `plugins/AlfacoShell/errors.py` | `ErrorCode` + `ERROR_CATALOG` + `error_message` |
| `plugins/AlfacoShell/domain.py` | **pur** : `resolve_exec_argv`, `prettify`, `format_result` |
| `plugins/AlfacoShell/commands/__init__.py` | package des commandes (vide) |
| `plugins/AlfacoShell/commands/run_selection.py` | adapter `TextCommand` (I/O subprocess + buffer) |
| `plugins/AlfacoShell/plugin.py` | entry-point : `plugin_loaded` (reload) + import commande |
| `plugins/AlfacoShell/alfaco-shell.sublime-settings` | défaut package (NON déployé) |
| `plugins/AlfacoShell/templates/User/alfaco-shell.sublime-settings` | seed posé dans `<Packages>/User/` |
| `plugins/AlfacoShell/Context.sublime-menu` | entrée clic droit |
| `plugins/AlfacoShell/Main.sublime-menu` | Tools → Alfaco → Shell + Preferences |
| `plugins/AlfacoShell/Default.sublime-commands` | Command Palette |
| `plugins/AlfacoShell/Default.sublime-keymap` | binding commenté (suggestion) |
| `plugins/AlfacoShell/package-metadata.json` | métadonnées suite (NON déployé) |
| `plugins/AlfacoShell/README.md` | doc style suite |
| `plugins/AlfacoShell/tests/test_domain.py` | tests du domain pur |
| `CLAUDE.md` | tableau des plugins (5 → 6) |

---

## Task 1 : Fondations — constants.py + errors.py

**Files:**
- Create: `plugins/AlfacoShell/.python-version`
- Create: `plugins/AlfacoShell/constants.py`
- Create: `plugins/AlfacoShell/errors.py`

- [ ] **Step 1 : Créer `.python-version`**

Contenu (une ligne) :

```
3.8
```

- [ ] **Step 2 : Créer `constants.py`**

```python
# -*- coding: utf-8 -*-
"""Constantes de configuration du plugin AlfacoShell.

Clés du fichier de settings, valeurs par défaut et identifiants du
package. Aucune logique ici — uniquement la source de vérité des noms.
"""

PLUGIN_NAME = "AlfacoShell"
SETTINGS_FILE = "alfaco-shell.sublime-settings"

# Clés du fichier de settings (source de vérité de la configuration)
KEY_EXEC_PREFIX = "exec_prefix"
KEY_EXEC_BY_PLATFORM = "exec_by_platform"
KEY_TIMEOUT = "timeout_seconds"

# Défauts (précédence : exec_prefix > exec_by_platform[os] > défaut intégré).
# Clés de plateforme = valeurs de sublime.platform() : "windows" | "osx" | "linux".
DEFAULT_EXEC_BY_PLATFORM = {
    "windows": ["wsl.exe", "-e", "bash", "-lc"],  # WSL, login shell → ~/.aws + PATH
    "osx": ["/bin/zsh", "-lc"],                    # zsh login → PATH Homebrew (aws)
    "linux": ["bash", "-lc"],
}
FALLBACK_PLATFORM = "linux"
DEFAULT_TIMEOUT_SECONDS = 120

# Buffer de sortie
OUTPUT_TITLE_PREFIX = "Shell ▸ "
OUTPUT_TITLE_MAXLEN = 40
OUTPUT_SYNTAX = "Packages/Text/Plain text.tmLanguage"
```

- [ ] **Step 3 : Créer `errors.py`**

```python
# -*- coding: utf-8 -*-
"""Codes d'erreur applicatifs et libellés UI du plugin AlfacoShell.

Convention des codes : ``DOMAINE_DESCRIPTION``. Les libellés humains
vivent dans :data:`ERROR_CATALOG` ; :func:`error_message` les formate.
"""


class ErrorCode:
    """Codes d'erreur applicatifs (convention : DOMAINE_DESCRIPTION)."""

    SELECTION_EMPTY = "SELECTION_EMPTY"
    EXEC_TIMEOUT = "EXEC_TIMEOUT"
    EXEC_FAILED = "EXEC_FAILED"


ERROR_CATALOG = {
    ErrorCode.SELECTION_EMPTY: "Aucune sélection à exécuter.",
    ErrorCode.EXEC_TIMEOUT: "Délai d'exécution dépassé.",
    ErrorCode.EXEC_FAILED: "Échec du runner.",
}


def error_message(code, detail=""):
    """Formate ``[CODE] libellé`` (+ ``: détail`` si fourni)."""
    base = "[{}] {}".format(code, ERROR_CATALOG[code])
    return "{} : {}".format(base, detail) if detail else base
```

- [ ] **Step 4 : Commit**

```bash
git add plugins/AlfacoShell/.python-version plugins/AlfacoShell/constants.py plugins/AlfacoShell/errors.py
git commit -m "feat(alfaco-shell): constantes et codes d'erreur du package"
```

---

## Task 2 : domain.py — `resolve_exec_argv` (TDD)

**Files:**
- Create: `plugins/AlfacoShell/tests/test_domain.py`
- Create: `plugins/AlfacoShell/domain.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `plugins/AlfacoShell/tests/test_domain.py` :

```python
"""Tests du domain pur d'AlfacoShell — exécutables hors Sublime : pytest."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from AlfacoShell.constants import DEFAULT_EXEC_BY_PLATFORM  # noqa: E402
from AlfacoShell.domain import resolve_exec_argv  # noqa: E402


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
```

- [ ] **Step 2 : Lancer le test → échec attendu**

Run: `pytest plugins/AlfacoShell/tests/test_domain.py -v`
Expected: FAIL (collection error — `No module named 'AlfacoShell.domain'`).

- [ ] **Step 3 : Implémenter `domain.py` (minimal)**

Créer `plugins/AlfacoShell/domain.py` :

```python
# -*- coding: utf-8 -*-
"""Domain pur du plugin AlfacoShell.

Ne dépend ni de Sublime, ni d'aucune I/O. Construit l'argv d'exécution
selon la plateforme, joliifie la sortie et formate le résultat du buffer.
100 % testable hors de l'éditeur.
"""
from .constants import (
    DEFAULT_EXEC_BY_PLATFORM,
    FALLBACK_PLATFORM,
    KEY_EXEC_BY_PLATFORM,
    KEY_EXEC_PREFIX,
)


def resolve_exec_argv(command_text, settings_like, platform):
    """argv d'exécution = préfixe résolu + [texte de commande].

    Précédence du préfixe :
      1. settings 'exec_prefix' (override global, tous OS) ;
      2. settings 'exec_by_platform'[platform] (override par OS) ;
      3. DEFAULT_EXEC_BY_PLATFORM[platform] (défaut intégré).
    Plateforme inconnue → repli sur FALLBACK_PLATFORM.

    settings_like expose .get(key, default) (compatible sublime.Settings et dict).
    """
    prefix = settings_like.get(KEY_EXEC_PREFIX, None)
    if not prefix:
        by_platform = settings_like.get(KEY_EXEC_BY_PLATFORM, None) or {}
        prefix = by_platform.get(platform)
    if not prefix:
        prefix = DEFAULT_EXEC_BY_PLATFORM.get(
            platform, DEFAULT_EXEC_BY_PLATFORM[FALLBACK_PLATFORM]
        )
    return list(prefix) + [command_text]
```

- [ ] **Step 4 : Lancer le test → succès attendu**

Run: `pytest plugins/AlfacoShell/tests/test_domain.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5 : Commit**

```bash
git add plugins/AlfacoShell/domain.py plugins/AlfacoShell/tests/test_domain.py
git commit -m "feat(alfaco-shell): résolution multi-OS de l'argv d'exécution (domain)"
```

---

## Task 3 : domain.py — `prettify` (TDD)

**Files:**
- Modify: `plugins/AlfacoShell/tests/test_domain.py`
- Modify: `plugins/AlfacoShell/domain.py`

- [ ] **Step 1 : Ajouter les tests qui échouent**

Dans `tests/test_domain.py`, ajouter `prettify` à l'import existant :

```python
from AlfacoShell.domain import prettify, resolve_exec_argv  # noqa: E402
```

Puis, en début de fichier après les imports, ajouter `import json` :

```python
import json
```

Et ajouter ces tests à la fin du fichier :

```python
# ── prettify ────────────────────────────────────────────────────────────────

def test_prettify_formats_valid_json():
    out = prettify('{"a":1}')
    assert json.loads(out) == {"a": 1}
    assert "\n" in out  # indenté


def test_prettify_passes_through_non_json():
    assert prettify("plain text") == "plain text"


def test_prettify_empty_returns_input():
    assert prettify("   ") == "   "
```

- [ ] **Step 2 : Lancer → échec attendu**

Run: `pytest plugins/AlfacoShell/tests/test_domain.py -k prettify -v`
Expected: FAIL (`cannot import name 'prettify'`).

- [ ] **Step 3 : Implémenter `prettify`**

Dans `domain.py`, ajouter `import json` en haut (avant l'import `from .constants`) :

```python
import json
```

Puis ajouter la fonction à la fin du module :

```python
def prettify(raw):
    """JSON indenté si parsable, sinon texte brut inchangé."""
    stripped = raw.strip()
    if not stripped:
        return raw
    try:
        return json.dumps(json.loads(stripped), indent=2, ensure_ascii=False)
    except (ValueError, TypeError):
        return raw
```

- [ ] **Step 4 : Lancer → succès attendu**

Run: `pytest plugins/AlfacoShell/tests/test_domain.py -v`
Expected: PASS (10 tests).

- [ ] **Step 5 : Commit**

```bash
git add plugins/AlfacoShell/domain.py plugins/AlfacoShell/tests/test_domain.py
git commit -m "feat(alfaco-shell): prettify JSON de la sortie (domain)"
```

---

## Task 4 : domain.py — `format_result` (TDD)

**Files:**
- Modify: `plugins/AlfacoShell/tests/test_domain.py`
- Modify: `plugins/AlfacoShell/domain.py`

- [ ] **Step 1 : Ajouter les tests qui échouent**

Mettre à jour l'import dans `tests/test_domain.py` :

```python
from AlfacoShell.domain import format_result, prettify, resolve_exec_argv  # noqa: E402
```

Ajouter ces tests à la fin :

```python
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
```

- [ ] **Step 2 : Lancer → échec attendu**

Run: `pytest plugins/AlfacoShell/tests/test_domain.py -k format_result -v`
Expected: FAIL (`cannot import name 'format_result'`).

- [ ] **Step 3 : Implémenter `format_result`**

Ajouter à la fin de `domain.py` :

```python
def format_result(stdout, stderr, returncode):
    """Texte du buffer : corps prettifié, bloc stderr (si présent), exit code."""
    parts = []
    body = prettify(stdout)
    if body.strip():
        parts.append(body)
    if stderr.strip():
        parts.append("--- stderr ---\n" + stderr.rstrip())
    parts.append("--- exit code: {} ---".format(returncode))
    return "\n".join(parts)
```

- [ ] **Step 4 : Lancer toute la suite du domain → succès**

Run: `pytest plugins/AlfacoShell/tests/test_domain.py -v`
Expected: PASS (13 tests).

- [ ] **Step 5 : Commit**

```bash
git add plugins/AlfacoShell/domain.py plugins/AlfacoShell/tests/test_domain.py
git commit -m "feat(alfaco-shell): formatage du buffer de résultat (domain)"
```

---

## Task 5 : Adapter Sublime — commande + entry-point

> Les `*Command` ne sont pas testables hors-Sublime (cf. CLAUDE.md) : pas de
> test pytest ici, la logique est déjà couverte dans `domain.py`. Validation
> manuelle dans Sublime listée en Task 9.

**Files:**
- Create: `plugins/AlfacoShell/commands/__init__.py`
- Create: `plugins/AlfacoShell/commands/run_selection.py`
- Create: `plugins/AlfacoShell/plugin.py`

- [ ] **Step 1 : Créer `commands/__init__.py` (vide)**

Fichier vide (paquet Python).

- [ ] **Step 2 : Créer `commands/run_selection.py`**

```python
# -*- coding: utf-8 -*-
"""Commande : exécuter la sélection courante comme commande shell.

Adapter Sublime : lit la sélection, lance le process en async (subprocess),
écrit le résultat dans un buffer scratch. Toute la logique pure vit dans
:mod:`AlfacoShell.domain`.
"""
import subprocess

import sublime
import sublime_plugin

from AlfacoShell import constants
from AlfacoShell.domain import format_result, resolve_exec_argv
from AlfacoShell.errors import ErrorCode, error_message


class AlfacoShellRunSelectionCommand(sublime_plugin.TextCommand):
    """Exécute la sélection courante comme commande shell (multi-OS)."""

    def run(self, edit):
        cmd_text = self._selected_text()
        if not cmd_text:
            sublime.status_message(error_message(ErrorCode.SELECTION_EMPTY))
            return
        sublime.status_message(constants.PLUGIN_NAME + " : exécution…")
        sublime.set_timeout_async(lambda: self._run_async(cmd_text), 0)

    def is_enabled(self):
        return any(not r.empty() for r in self.view.sel())

    def _selected_text(self):
        regions = [r for r in self.view.sel() if not r.empty()]
        return "\n".join(self.view.substr(r) for r in regions).strip()

    def _run_async(self, cmd_text):
        settings = sublime.load_settings(constants.SETTINGS_FILE)
        argv = resolve_exec_argv(cmd_text, settings, sublime.platform())
        timeout = settings.get(constants.KEY_TIMEOUT, constants.DEFAULT_TIMEOUT_SECONDS)
        try:
            proc = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            out = proc.stdout.decode("utf-8", "replace")
            err = proc.stderr.decode("utf-8", "replace")
            result = format_result(out, err, proc.returncode)
        except subprocess.TimeoutExpired:
            result = error_message(ErrorCode.EXEC_TIMEOUT)
        except Exception as exc:  # noqa: BLE001 — reporté dans le buffer
            result = error_message(ErrorCode.EXEC_FAILED, str(exc))
        sublime.set_timeout(lambda: self._show(cmd_text, result), 0)

    def _show(self, cmd_text, result):
        window = self.view.window()
        out = window.new_file()
        out.set_scratch(True)
        out.set_name(constants.OUTPUT_TITLE_PREFIX + cmd_text[: constants.OUTPUT_TITLE_MAXLEN])
        out.assign_syntax(constants.OUTPUT_SYNTAX)
        out.run_command("append", {"characters": result})
        out.set_read_only(True)
```

- [ ] **Step 3 : Créer `plugin.py`**

```python
# -*- coding: utf-8 -*-
"""Entry point du plugin AlfacoShell (suite Alfaco).

Plugin autonome : exécute la sélection courante comme commande shell et
affiche le résultat dans un buffer scratch. Exécution multi-OS (zsh sur
macOS, bash sur Linux, WSL sur Windows), surchargeable dans
``alfaco-shell.sublime-settings`` (User/).

Contrairement aux plugins consommateurs d'``AlfacoLib``, AlfacoShell ne
dépend de rien d'autre que la stdlib, et lit ses settings via
``sublime.load_settings`` à chaque exécution.

Compatibilité : Sublime Text 4, plugin host Python 3.8 (.python-version).
"""
import importlib

import sublime  # noqa: F401  (réservé pour usages futurs)

from AlfacoShell import constants as _constants
from AlfacoShell import errors as _errors
from AlfacoShell import domain as _domain

# Sublime ne cascade pas les reloads des sous-modules d'un package : on les
# recharge explicitement au chargement du plugin.
_LOCAL_MODULES = (_constants, _errors, _domain)


def plugin_loaded():
    for mod in _LOCAL_MODULES:
        importlib.reload(mod)


# Déclenche la découverte de la classe *Command par Sublime.
from AlfacoShell.commands.run_selection import AlfacoShellRunSelectionCommand  # noqa: E402, F401
```

- [ ] **Step 4 : Vérifier que la suite pytest reste verte**

Run: `make test`
Expected: PASS (la suite existante + 13 tests AlfacoShell ; aucun import cassé).

- [ ] **Step 5 : Commit**

```bash
git add plugins/AlfacoShell/commands plugins/AlfacoShell/plugin.py
git commit -m "feat(alfaco-shell): commande run_selection + entry-point"
```

---

## Task 6 : Settings (défaut package + seed User)

**Files:**
- Create: `plugins/AlfacoShell/alfaco-shell.sublime-settings`
- Create: `plugins/AlfacoShell/templates/User/alfaco-shell.sublime-settings`

- [ ] **Step 1 : Créer le défaut package `alfaco-shell.sublime-settings`**

```jsonc
{
    // AlfacoShell — exécuter la sélection comme commande shell.
    // Précédence du préfixe : exec_prefix > exec_by_platform[os] > défaut intégré.

    // Override global (tous OS). Décommenter pour forcer un préfixe unique.
    // "exec_prefix": ["wsl.exe", "-e", "bash", "-c"],

    // Override par plateforme (clés Sublime : "windows" | "osx" | "linux").
    // Seules les clés présentes priment ; les autres OS gardent le défaut intégré.
    "exec_by_platform": {
        "windows": ["wsl.exe", "-e", "bash", "-lc"],
        "osx": ["/bin/zsh", "-lc"],
        "linux": ["bash", "-lc"]
    },

    // Timeout du process (secondes).
    "timeout_seconds": 120
}
```

- [ ] **Step 2 : Créer le seed User `templates/User/alfaco-shell.sublime-settings`**

Contenu **identique** au Step 1 (c'est ce fichier que `init-config` pose dans
`<Packages>/User/`, jamais écrasé par `make install`).

```jsonc
{
    // AlfacoShell — exécuter la sélection comme commande shell.
    // Précédence du préfixe : exec_prefix > exec_by_platform[os] > défaut intégré.

    // Override global (tous OS). Décommenter pour forcer un préfixe unique.
    // "exec_prefix": ["wsl.exe", "-e", "bash", "-c"],

    // Override par plateforme (clés Sublime : "windows" | "osx" | "linux").
    // Seules les clés présentes priment ; les autres OS gardent le défaut intégré.
    "exec_by_platform": {
        "windows": ["wsl.exe", "-e", "bash", "-lc"],
        "osx": ["/bin/zsh", "-lc"],
        "linux": ["bash", "-lc"]
    },

    // Timeout du process (secondes).
    "timeout_seconds": 120
}
```

- [ ] **Step 3 : Commit**

```bash
git add plugins/AlfacoShell/alfaco-shell.sublime-settings plugins/AlfacoShell/templates
git commit -m "feat(alfaco-shell): settings par défaut + seed User (multi-OS)"
```

---

## Task 7 : UI — menus, palette, keymap, metadata

**Files:**
- Create: `plugins/AlfacoShell/Context.sublime-menu`
- Create: `plugins/AlfacoShell/Main.sublime-menu`
- Create: `plugins/AlfacoShell/Default.sublime-commands`
- Create: `plugins/AlfacoShell/Default.sublime-keymap`
- Create: `plugins/AlfacoShell/package-metadata.json`

- [ ] **Step 1 : `Context.sublime-menu`**

```json
[
    { "caption": "-", "id": "alfaco_shell_separator" },
    {
        "caption": "Shell : exécuter la sélection",
        "command": "alfaco_shell_run_selection"
    }
]
```

- [ ] **Step 2 : `Main.sublime-menu`**

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
                        "caption": "Shell",
                        "id": "alfaco-shell",
                        "children": [
                            { "caption": "Exécuter la sélection", "command": "alfaco_shell_run_selection" }
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
                        "caption": "AlfacoShell",
                        "id": "alfaco-shell",
                        "children": [
                            { "caption": "Settings – Default", "args": { "file": "${packages}/AlfacoShell/alfaco-shell.sublime-settings" }, "command": "open_file" },
                            { "caption": "Settings – User", "args": { "file": "${packages}/User/alfaco-shell.sublime-settings" }, "command": "open_file" }
                        ]
                    }
                ]
            }
        ]
    }
]
```

- [ ] **Step 3 : `Default.sublime-commands`**

```json
[
    {
        "caption": "AlfacoShell: Exécuter la sélection",
        "command": "alfaco_shell_run_selection"
    },
    {
        "caption": "AlfacoShell: Ouvrir les settings (User)",
        "command": "open_file",
        "args": { "file": "${packages}/User/alfaco-shell.sublime-settings" }
    }
]
```

- [ ] **Step 4 : `Default.sublime-keymap`**

```json
[
    // Aucun binding par défaut : l'espace de touches est partagé entre tous les
    // plugins Alfaco (risque de collision, cf. CLAUDE.md). Décommenter/adapter
    // pour ajouter un raccourci en plus de la palette.
    // { "keys": ["ctrl+alt+a"], "command": "alfaco_shell_run_selection" }
]
```

- [ ] **Step 5 : `package-metadata.json`** (autonome — pas de `dependencies_alfaco`)

```json
{
    "name": "AlfacoShell",
    "version": "1.0.0",
    "description": "Plugin Sublime Text d'exécution de la sélection comme commande shell (suite Alfaco)",
    "sublime_text": ">=4000",
    "platforms": ["*"]
}
```

- [ ] **Step 6 : Commit**

```bash
git add plugins/AlfacoShell/Context.sublime-menu plugins/AlfacoShell/Main.sublime-menu plugins/AlfacoShell/Default.sublime-commands plugins/AlfacoShell/Default.sublime-keymap plugins/AlfacoShell/package-metadata.json
git commit -m "feat(alfaco-shell): menus, palette, keymap et métadonnées"
```

---

## Task 8 : README (style suite)

**Files:**
- Create: `plugins/AlfacoShell/README.md`

- [ ] **Step 1 : Créer `README.md`**

```markdown
# AlfacoShell — plugin Sublime Text 4 (suite Alfaco)

Exécute le **texte sélectionné comme commande shell** et affiche le résultat
dans un buffer scratch (JSON indenté si parsable, sinon brut), suivi de
`stderr` (si présent) et du code de sortie. Exécution **asynchrone** :
l'éditeur ne gèle pas.

Multi-OS : **macOS** (`/bin/zsh -lc`), **Linux** (`bash -lc`), **Windows via
WSL** (`wsl.exe -e bash -lc`). Le préfixe d'exécution est entièrement
configurable.

Plugin **autonome** : il ne dépend pas d'`AlfacoLib`.

## Fonctionnalités

- Exécute une ou plusieurs régions sélectionnées (concaténées) comme commande.
- Accessible par **clic droit**, **Tools → Alfaco → Shell** ou **Command Palette**.
- Sortie JSON jolie si parsable, sinon texte brut ; `--- stderr ---` et
  `--- exit code: N ---` ajoutés.
- Préfixe d'exécution résolu **par OS**, surchargeable.

## Installation (monorepo)

```bash
make install PLUGIN=AlfacoShell       # copie le plugin + seed la config User/
# ou, hors WSL :
make link PLUGIN=AlfacoShell          # symlink (mode dev)
```

`make install` exécute `init-config` : le fichier de config par défaut est
copié dans `<Packages>/User/alfaco-shell.sublime-settings` (sans écraser un
fichier existant).

## Utilisation

1. Sélectionner une commande, ex. `aws ec2 describe-instances --region eu-west-1`.
2. Command Palette (`Ctrl+Shift+P`) → **AlfacoShell: Exécuter la sélection**
   (ou clic droit, ou Tools → Alfaco → Shell).
3. Un buffer scratch `Shell ▸ …` s'ouvre avec la sortie.

## Configuration

`Preferences → Package Settings → AlfacoShell → Settings – User`

```jsonc
{
    // Override global (tous OS) — prioritaire sur tout le reste.
    // "exec_prefix": ["wsl.exe", "-e", "bash", "-c"],

    // Override par plateforme ("windows" | "osx" | "linux").
    "exec_by_platform": {
        "windows": ["wsl.exe", "-e", "bash", "-lc"],
        "osx": ["/bin/zsh", "-lc"],
        "linux": ["bash", "-lc"]
    },

    "timeout_seconds": 120
}
```

Précédence : `exec_prefix` > `exec_by_platform[os]` > défaut intégré.
`-lc` charge le login shell (donc `PATH`, `~/.aws/config`, variables d'env).

## Architecture

| Couche | Fichier | Rôle |
|--------|---------|------|
| Domain (pur) | `domain.py` | argv par OS, prettify JSON, formatage |
| Adapter | `commands/run_selection.py` | I/O Sublime, subprocess async, buffer |
| Entry-point | `plugin.py` | `plugin_loaded` (reload) + découverte commande |
| Config | `alfaco-shell.sublime-settings` | params surchargeables (non déployé) |
| Interface | `*.sublime-menu` / `Default.sublime-commands` | palette + menus |
| Tests | `tests/test_domain.py` | pytest sur le domain |

Le domain n'importe ni Sublime ni `subprocess` → testable hors éditeur :
`pytest plugins/AlfacoShell/tests/`.

## Erreurs codifiées

| Code | Sens |
|------|------|
| `SELECTION_EMPTY` | Aucune sélection à exécuter |
| `EXEC_TIMEOUT` | Délai d'exécution dépassé |
| `EXEC_FAILED` | Échec du runner |

## Références officielles

- API Sublime Text : <https://www.sublimetext.com/docs/api_reference.html>
- AWS CLI Command Reference : <https://docs.aws.amazon.com/cli/latest/reference/>
```

- [ ] **Step 2 : Commit**

```bash
git add plugins/AlfacoShell/README.md
git commit -m "docs(alfaco-shell): README du plugin"
```

---

## Task 9 : Intégration suite — CLAUDE.md + vérification déploiement

**Files:**
- Modify: `CLAUDE.md` (tableau des plugins + compte)

- [ ] **Step 1 : Mettre à jour le compte de plugins dans `CLAUDE.md`**

Remplacer (section « What this is ») :

```
A **monorepo** of 5 Sublime Text 4 plugins (the "Alfaco suite")
```

par :

```
A **monorepo** of 6 Sublime Text 4 plugins (the "Alfaco suite")
```

- [ ] **Step 2 : Ajouter la ligne AlfacoShell au tableau des plugins**

Dans le tableau Markdown des plugins de `CLAUDE.md`, ajouter après la ligne
`AlfacoTemplates` :

```
| `AlfacoShell` | Exécute la sélection courante comme commande shell (multi-OS : zsh macOS / bash Linux / WSL Windows) et affiche le résultat (JSON indenté si parsable) dans un buffer scratch. **Standalone — no `AlfacoLib` dependency.** |
```

- [ ] **Step 3 : Vérifier la découverte par deploy.py**

Run: `python tools/deploy.py status`
Expected: `AlfacoShell` apparaît dans la liste (statut `absent` ou `copy`/`link`).

- [ ] **Step 4 : Lancer toute la suite de tests**

Run: `make test`
Expected: PASS (suite existante + 13 tests AlfacoShell).

- [ ] **Step 5 : Déployer (⚠️ fermer Sublime Text d'abord — cf. note ci-dessous)**

> **Windows/WSL** : fermer Sublime Text avant `make install`. Sublime garde
> `plugin.py` ouvert (module chargé) ; pendant la réécriture, une course avec
> son file-watcher provoque un `PermissionError` à la suppression. Re-lancer
> `make install` suffit à réparer un dossier laissé partiel.

Run: `make install PLUGIN=AlfacoShell`
Expected: `AlfacoShell` copié + `init-config` pose
`<Packages>/User/alfaco-shell.sublime-settings`.

- [ ] **Step 6 : Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): ajoute AlfacoShell au tableau des plugins (6 plugins)"
```

---

## Task 10 : Validation manuelle dans Sublime (humain)

> Non automatisable hors-Sublime. À faire par l'utilisateur après `make install`
> et reload de l'éditeur.

- [ ] Recharger Sublime (ou redémarrer). Vérifier la console : pas d'erreur de
  chargement `AlfacoShell`.
- [ ] Sélectionner `echo bonjour` → Command Palette → **AlfacoShell: Exécuter la
  sélection** → buffer `Shell ▸ echo bonjour` affiche `bonjour` + `--- exit code: 0 ---`.
- [ ] Sélectionner une commande JSON (ex. `aws sts get-caller-identity` ou
  `echo '{"a":1}'`) → sortie indentée.
- [ ] Sans sélection → message de statut `[SELECTION_EMPTY] …`, aucun buffer.
- [ ] Clic droit → entrée « Shell : exécuter la sélection » présente.
- [ ] Tools → Alfaco → Shell → Exécuter la sélection présent.
- [ ] Preferences → Package Settings → AlfacoShell → ouvre Default / User.

---

## Self-Review (effectuée)

- **Couverture spec :** cadrage neutre (Task 1/5/8), exécution multi-OS + précédence (Task 2), prettify (Task 3), format_result (Task 4), adapter async + buffer `Shell ▸` plain text (Task 5), settings package+seed (Task 6), menus/palette/keymap sans binding (Task 7), README (Task 8), CLAUDE.md + déploiement (Task 9), validation manuelle (Task 10). Erreurs codifiées `SELECTION_EMPTY`/`EXEC_TIMEOUT`/`EXEC_FAILED` (Task 1, utilisées Task 5).
- **Placeholders :** aucun — tout le code est fourni intégralement.
- **Cohérence des types :** `resolve_exec_argv(command_text, settings_like, platform)`, `prettify(raw)`, `format_result(stdout, stderr, returncode)`, `error_message(code, detail="")`, classe `AlfacoShellRunSelectionCommand` / commande `alfaco_shell_run_selection`, constantes (`KEY_TIMEOUT`, `DEFAULT_TIMEOUT_SECONDS`, `OUTPUT_*`) — noms identiques entre définition (Task 1/2) et usage (Task 5).

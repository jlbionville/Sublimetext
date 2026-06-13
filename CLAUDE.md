# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **monorepo** of 5 Sublime Text 4 plugins (the "Alfaco suite"), refactored from a single monolithic package. Each plugin is its own deployable Sublime package with its own commands, settings, keymaps, snippets, macros, and menus.

| Plugin | Purpose |
|---|---|
| `AlfacoLib` | Shared library: `Configuration`, Atlassian REST client, IO helpers, logger. **No user commands.** |
| `AlfacoAtlassian` | Jira/Confluence REST workflows: select org/project, create issues depuis JSON ou Markdown (templates). |
| `AlfacoEditing` | Editor utilities: text-to-table, `<start>`/`<end>` markers, date insertion, tag handling. |
| `AlfacoCompletion` | Static Python autocompletion (demo `EventListener`). |
| `AlfacoAwsCli` | AWS CLI command templates from a quick panel (placeholders `${nom}`, modes `snippet`/`guided`, selection→params, batch, `.sublime-snippet` import/export). **Standalone — no `AlfacoLib` dependency.** |

Code, comments and UI captions are in **French** — keep that style when editing.

## Run / install

No build step. The repo is a monorepo of Sublime packages.

```bash
make link              # symlinks plugins/* → <Packages>/  (Linux/macOS)
make install           # copy plugins/* → <Packages>/    (WSL/Windows)
make uninstall         # remove all <Packages>/Alfaco*
make status            # which plugin is link/copy/absent
make init-config       # copy plugins/<X>/templates/User/* → <Packages>/User/  (skip-if-exists)
make init-config-force # same, overwrites existing
make test              # pytest hors-Sublime
make new-plugin NAME=X # scaffold plugins/AlfacoX/
```

User config templates live under `plugins/<X>/templates/User/<setting>.sublime-settings` (excluded from deployment). They contain placeholders + JSONC comments — never real secrets.

**Settings deployment**: the package default `plugins/<X>/alfaco-<X>.sublime-settings` is **not deployed** (`tools/deploy.py` excludes `*.sublime-settings`). All config lives in `<Packages>/User/`, which `make install` never overwrites — and `install` runs `init-config` (skip-if-exists) so the User file is seeded on first install. Without a `User/` file, `atlassian.organisations` is empty (graceful error), so `make init-config` is the required config step.

Variable `PLUGIN=AlfacoEditing` to target a single plugin: `make link PLUGIN=AlfacoEditing`.

`make link` detects WSL and forces `make install` (NTFS doesn't follow WSL symlinks). The Windows username is resolved via `cmd.exe` (handles the case where `$USER=ubuntu` but Windows user is `Jean`). Override with `SUBLIME_PACKAGES_DIR` if needed. See `docs/deployment.md`.

`AlfacoLib.atlassian_client` uses **stdlib `urllib`** (no `requests` dep). The Sublime Text 4 plugin host doesn't ship `requests`, and pulling it in via Package Control conflicts with our `make install` (manual copy) deployment.

Package Control cohabite sans rien à faire : les `package-metadata.json` sont **exclus du déploiement** (`tools/deploy.py:EXCLUDE_DURING_DEPLOY`), donc PC ne reconnaît pas nos plugins comme « gérés par lui » et les laisse comme tout dossier manuel (comparable à `MyBookmarks`). Sans cette exclusion, PC les supprimait au démarrage comme « orphelins ». Voir `docs/installation.md`.

## Architecture

**Topology:** `AlfacoLib` is a Sublime package itself, imported by the others via `from AlfacoLib.config import Configuration`. The naming convention is **CamelCase without dashes** because Python doesn't allow `-` in module names (`from Alfaco-Lib.x` is invalid).

```
plugins/AlfacoLib/   ← shared, no user commands
plugins/AlfacoAtlassian/
plugins/AlfacoEditing/
plugins/AlfacoCompletion/
tools/deploy.py      ← link/install/uninstall/status, multi-OS
tools/new_plugin.py  ← scaffold from tools/templates/plugin/
```

**Each consumer plugin's `plugin.py`** boilerplate:

```python
import importlib
from AlfacoLib import config as _alfacolib_config
# ... other lib imports

_LIB_MODULES = (_alfacolib_config, ...)
config = None

def plugin_loaded():
    global config
    for mod in _LIB_MODULES:
        importlib.reload(mod)         # crucial: Sublime doesn't cascade reloads
    config = _alfacolib_config.Configuration([
        "alfaco-<plugin>.sublime-settings",
        "Preferences.sublime-settings",
    ])

# Trigger Sublime auto-discovery of *Command classes:
from <Plugin>.commands.foo import FooCommand  # noqa: F401
```

**One command = one file** in `plugins/<Plugin>/commands/`. They're imported in `plugin.py` so Sublime discovers the classes.

**Plugin host** is **Python 3.8** (`.python-version` file in each plugin). All plugins must share the same host to import each other.

**`Configuration` lookup order**: runtime (set by `config.set()`) → settings layers (in declaration order) → default. No side effect on `Preferences.sublime-settings` (the legacy did, this no longer does).

See `docs/architecture.md` for the full picture and `docs/superpowers/specs/2026-05-08-multi-plugins-monorepo-design.md` for the original design rationale.

## Tests

`pytest` runs hors-Sublime via the root `conftest.py` which stubs `sublime` and `sublime_plugin` with `MagicMock`. Tests live in `plugins/<Plugin>/tests/` and are excluded from deployment.

```bash
make test                              # full suite (~31 tests)
pytest plugins/AlfacoLib/tests/        # one plugin
pytest -k "test_my_function"           # by name
```

Atlassian client tests use `unittest.mock.patch` on `AlfacoLib.atlassian_client.urlopen`. Sublime commands (`*Command`) are not testable hors-Sublime — extract pure logic to test it.

## Pitfalls / gotchas

- **`.python-version` was in `.gitignore`** (pyenv rule) — commented out because Sublime needs it. Don't reintroduce the rule.
- **WSL → Windows symlinks don't work**: `make link` auto-falls back to `make install`. Don't manually symlink across `/mnt/c/`.
- **Modifying `AlfacoLib` doesn't cascade-reload consumers** in Sublime. Save a `.py` in the consumer plugin to retrigger `plugin_loaded()` (which does the `importlib.reload()`).
- **Adding a command**: don't forget to import it in `plugin.py` (otherwise Sublime won't see it) and to update **all 3 OS keymaps** if it has a binding.
- **Keymaps partagés entre plugins** : tous les `Alfaco*` partagent un seul espace de touches ; une collision sur une même touche **sans `context`** se résout par ordre de chargement **alphabétique des packages** (le dernier gagne). Pour cohabiter sur une même touche, ajouter un `context` (ex. `init_markdown_jira` est sur `Ctrl+M` avec un selector `text.html.markdown`, ce qui préserve le `move_to brackets` natif ailleurs). Voir `docs/troubleshooting.md`.
- **Ne pas réintroduire `startdate`** dans les payloads/templates Jira : champ non standard (customfield selon l'instance) → `400`. Retiré en PR #20 ; `duedate` (J+10) est conservé.
- **`Main.sublime-menu`** is auto-merged across packages by Sublime. Each plugin declares its own branch under `Tools → Alfaco → <plugin>`.
- **Package Control orphans** : PC ne supprime un dossier de `Packages/` au démarrage **que** s'il contient un `package-metadata.json` (marqueur « géré par PC ») et que le nom n'est pas dans `installed_packages`. Notre `tools/deploy.py` exclut explicitement `package-metadata.json` du déploiement pour cette raison — ne pas le réintroduire sans aussi documenter le patch `installed_packages`.

## Known follow-ups (not blocking)

- Windows: junctions are reported as `copy` by `make status` (Python <3.12 doesn't recognize them as symlinks).
- Manual Sublime validation (Tasks 18 + 25 of the implementation plan) hasn't been done yet — see `docs/superpowers/plans/2026-05-08-multi-plugins-monorepo.md`.

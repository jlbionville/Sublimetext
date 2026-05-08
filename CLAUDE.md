# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Sublime Text 3+ package named **Alfaco** that drives Atlassian (Jira/Confluence) REST APIs from the editor — selecting an organisation, picking a Jira project, posting JSON payloads from the active buffer, formatting output. The package also bundles a few unrelated editing helpers (text-to-table, date insertion, marker selection).

Code, comments and UI captions are in **French** — keep that style when editing.

## Install / run

There is no build, no test suite, no lint configuration. The repo *is* the package and runs inside Sublime's embedded Python (3.3 plugin host).

To work on it locally, clone (or symlink) the repo into Sublime's `Packages/` directory as `Alfaco/` (e.g. `~/.config/sublime-text/Packages/Alfaco` on Linux, `%APPDATA%\Sublime Text\Packages\Alfaco` on Windows). Sublime auto-reloads `*.py` files on save; check the console (`Ctrl+\``) for `plugin_loaded()` output and `print()` traces.

The `requests` library is imported by `modules/tools.py` — Sublime does not ship it, so it must already be available in the plugin host (typically vendored via `Package Control` dependency, but `package-metadata.json` declares no dependency — investigate before assuming it works on a fresh install).

## Architecture

**Single entry point: `AlfacoPlugins.py`**
- `plugin_loaded()` is the Sublime lifecycle hook. It loads three settings files into module globals (`settings_alfaco`, `settings_sublime`, `settings_atlassian`) and instantiates a single `Configuration` object used by every command.
- All user-facing commands are `sublime_plugin.TextCommand` / `WindowCommand` subclasses in this file. The class name → command name mapping follows Sublime's snake_case convention (e.g. `GetJiraListForOrganisationCommand` → `get_jira_list_for_organisation`).

**Three-layer settings lookup (`getSetting(key)`):**
1. `alfaco.sublime-settings` — user-level overrides (delimiter, json output folder).
2. `Preferences.sublime-settings` — Sublime global prefs; also where `setSetting()` writes (e.g. `organisation`).
3. `alfaco-atlassian.sublime-settings` — Atlassian organisations catalog and Jira defaults.

When adding a new setting, decide the layer first — secrets like `jira_password` must come from the **user's** `User/alfaco.sublime-settings` (never commit the default).

**`modules/configuration.py` — `Configuration` singleton:**
- Holds runtime state assembled across commands: selected organisation (`default_organisation`), selected project (`project_key`), API version, headers, auth tuple.
- `getBaseUrlForRESTApi()` builds `https://{default_organisation}.atlassian.net/rest/api/{api_rest_version}/` — every Atlassian call goes through this.
- The class has incomplete refactoring: commented-out `__init__` overloads and broken `setOrganisation` / `getOrganisationJiraProjects` (missing `self`). Do not rely on them.

**`modules/tools.py` — HTTP helpers:**
- `callApiRest(body, config, http_verb)` and `getUrlToGetJiraProjects(config)` wrap `requests`.
- Both pass `verify=False` (TLS verification disabled). Treat that as a known quirk; do not "fix" it without checking with the user — it may be required for a corporate proxy.

**Command-trigger surfaces:**
- `Default (Linux|Windows|OSX).sublime-keymap` — keybindings (the three files diverge; Windows has the most bindings, OSX the fewest, Linux a middle subset). When adding a binding, update all three.
- `Main.sublime-menu` — Tools → Alfaco menu and Preferences → Package Settings entries.
- `Context.sublime-menu` / `Side Bar.sublime-menu` — right-click menus.
- `Default.sublime-commands` — command palette entries.
- `macros/*.sublime-macro` — recorded multi-step actions.
- `snippets/**/*.sublime-snippet` — Jira/Confluence JSON payload templates referenced by name (e.g. `Packages/Alfaco/snippets/jira/jira.sublime-snippet`).

## Pitfalls to know

- **`AppelRestApiCommand` writes to `path_json_files_folder` using Windows backslashes** (`"{}\\error_api_call_...".format(...)`). The default value `H:\\Mon Drive\\jira` is Windows-only. On non-Windows, override in user settings or the file-write step crashes after the API call succeeds.
- **`ShowSelectedInputCommand` has a typo bug**: `nput_view = ...` then `input_view.add_regions(...)`. It will `NameError` if invoked.
- **`plugin_loaded()` calls `setSetting("organisation","business-projects")`** — this mutates the user's `Preferences.sublime-settings` on every load. Be aware before "fixing" it.
- The README is a stub (section headers only). Don't trust it for behavior.

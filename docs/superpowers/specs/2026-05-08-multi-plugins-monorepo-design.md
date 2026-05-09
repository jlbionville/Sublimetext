# Refactorisation : monorepo multi-plugins Sublime Text

- **Date** : 2026-05-08
- **Statut** : design approuvé, prêt pour planification d'implémentation
- **Branche cible** : `refactor/multi-plugins` (depuis `development`)
- **Auteur** : brainstorming Alfaco

## Contexte

Le dépôt actuel héberge un unique package Sublime Text **Alfaco** qui mélange trois domaines fonctionnels :
1. Pilotage des API Atlassian (Jira / Confluence) — `AlfacoPlugins.py`, `modules/`, snippets `jira/` et `confluence/`.
2. Utilitaires d'édition (text-to-table, marqueurs `<start>`/`<end>`, insertion de date, gestion de tags) — éparpillés entre `AlfacoPlugins.py` et `text_to_table.py`.
3. Auto-complétion Python — `AlfacoCompletion.py`.

Limites de la structure actuelle :
- Toute évolution touche un fichier monolithique (`AlfacoPlugins.py`, ~250 lignes) et trois keymaps divergentes par OS.
- Impossible d'installer une partie seulement (tout ou rien).
- Code partagé (`Configuration`, client REST) dispo uniquement pour ce package : pas de réutilisation.
- Plusieurs bugs / dette documentés dans `docs/troubleshooting.md` (login codé en dur, `verify=False`, pas de `timeout`, méthodes cassées de `Configuration`, snippets en doublon, typo `nput_view`…).

## Objectifs

1. **Découper** le projet en plusieurs packages Sublime Text indépendants, déployables séparément.
2. **Mutualiser** le code commun via un package « bibliothèque » dédié.
3. **Outiller** le monorepo : déploiement multi-OS, scaffold de nouveaux plugins, tests unitaires.
4. **Profiter** de la migration pour corriger la dette technique connue.
5. **Préparer** l'ajout futur de plugins (`AlfacoGit`, `AlfacoMarkdown`, …) sans nouveau refactor.

## Non-objectifs

- Publication sur Package Control (réservée pour plus tard — la structure le permettra mais on ne le fait pas dans ce travail).
- Tests d'intégration headless avec `UnitTesting` (documenté comme évolution possible, pas implémenté).
- Compatibilité Sublime Text 3 (Python 3.3) — on cible **uniquement** Sublime Text 4 + plugin host Python 3.8.
- Script PowerShell équivalent au `Makefile` (le déploiement utilise `make` + `tools/deploy.py` Python ; un Windows pur sans WSL/Git Bash devra installer `make` ou appeler `python tools/deploy.py` directement).

## Décisions structurantes

| # | Décision | Justification |
|---|---|---|
| D1 | **Monorepo** unique, un seul repo git (celui-ci, transformé). | Atomicité des changements cross-plugins, un seul `git log`, une seule CI à câbler. |
| D2 | **Plusieurs packages Sublime indépendants** déployés depuis `plugins/<NomPackage>/`. | Permet l'installation sélective + isolation Sublime native (un `plugin_loaded` par plugin, settings/menus séparés). |
| D3 | **Code partagé via package Sublime dédié** `AlfacoLib`. | Les autres plugins l'importent via `from AlfacoLib.config import Configuration`. Pattern utilisé par `Default`, `LSP`, `PackageControl`. |
| D4 | **Noms de packages en CamelCase sans tiret**. | Contrainte Python : `from Alfaco-Lib.x import y` est invalide. Convention Sublime officielle. |
| D5 | **Plugin host Python 3.8** uniquement (`.python-version` à la racine de chaque plugin). | Tous les packages qui s'importent mutuellement doivent partager le même host. ST 3 (Python 3.3) est legacy. |
| D6 | **Une commande = un fichier** dans `plugins/<Plugin>/commands/`. | Lisibilité (pas de scroll), testabilité unitaire, diff git focalisé. Sublime auto-découvre les classes `*Command` peu importe le nom du fichier. |
| D7 | **`importlib.reload()` dès le départ** dans le `plugin_loaded` de chaque consommateur de la lib. | Évite les modules de lib en cache après modification. Surcoût minimal (~5 lignes de boilerplate par plugin). |
| D8 | **`Makefile` dual-mode** : `make link` (symlinks pour le dev) + `make install` (copie pour install propre). | Couvre dev + déploiement utilisateur sans script supplémentaire. |
| D9 | **Logique multi-OS dans `tools/deploy.py`** (Python), `Makefile` n'est qu'une fine couche ergonomique. | Évite de dupliquer la logique de détection d'OS / chemins en `make` (peu portable). |
| D10 | **Un `tests/` par plugin** (pas de `tests/` racine). | Cohérence : chaque plugin embarque ses tests, ils sont exclus du déploiement. |
| D11 | **Renommage des classes** pendant la migration (casse les keymaps existants assumée). | Lisibilité long terme. Seul utilisateur impacté : l'auteur, sur sa machine. |
| D12 | **Bugs corrigés pendant la migration**, pas dans un commit séparé. | Évite un cycle « migrer puis corriger » qui doublerait le travail de validation. |
| D13 | **Doublons de snippets nettoyés** dans la migration (`snippets/jira.sublime-snippet`, `page.sublime-snippet`, etc. supprimés). | Comportement non-déterministe documenté dans `troubleshooting.md`, à éliminer. |
| D14 | **Une seule branche `refactor/multi-plugins`** depuis `development`, merge final via PR. | Préserve `main` et `development` pendant la migration. |

## Architecture cible

### Topologie

```
┌─────────────────────────────────────────────────────────────┐
│  Sublime Text  ─  dossier Packages/                          │
│                                                              │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ AlfacoLib/  │◄─┤ AlfacoAtlassian/ │  │AlfacoEditing/│   │
│  │             │  │                  │  │              │   │
│  │ • config    │  │ • commandes Jira │  │ • text_to_   │   │
│  │ • client    │  │ • snippets       │  │   table      │   │
│  │   REST      │  │ • settings JSON  │  │ • marqueurs  │   │
│  │ • io        │  │ • keymaps        │  │ • dates      │   │
│  │ • settings  │  │ • menus          │  │ • snippets   │   │
│  │ • logger    │  │ • macros         │  │ • macros     │   │
│  └─────────────┘  └──────────────────┘  └──────────────┘   │
│         ▲                                                    │
│         │              ┌────────────────┐                    │
│         └──────────────┤AlfacoCompletion│                    │
│                        │ • EventListener│                    │
│                        └────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

`AlfacoLib` n'expose **aucune commande utilisateur**. Les autres plugins sont autonomes côté ressources Sublime.

### Structure du dépôt

```
Sublimetext/                          ← le dépôt git actuel devient le monorepo
├── plugins/                          ← un sous-dossier = un package Sublime déployable
│   ├── AlfacoLib/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── atlassian_client.py
│   │   ├── settings.py
│   │   ├── io.py
│   │   ├── logger.py
│   │   ├── tests/
│   │   │   ├── conftest.py           ← stub `sublime` pour pytest
│   │   │   ├── test_config.py
│   │   │   └── test_atlassian_client.py
│   │   ├── .python-version           ← "3.8"
│   │   ├── package-metadata.json
│   │   └── README.md
│   │
│   ├── AlfacoAtlassian/
│   │   ├── plugin.py                 ← entry point, plugin_loaded, importlib.reload
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── create_jira_issue.py       ← ex-AppelRestApiCommand
│   │   │   ├── select_organisation.py     ← ex-GetListOrganisationCommand
│   │   │   ├── select_jira_project.py     ← ex-GetJiraListForOrganisationCommand
│   │   │   ├── open_jira_projects.py      ← print(password) retiré
│   │   │   ├── init_json_jira.py
│   │   │   └── set_jira_project_in_snippet.py
│   │   ├── snippets/
│   │   │   ├── jira/jira.sublime-snippet
│   │   │   └── confluence/{page,childPage,space}.sublime-snippet
│   │   ├── macros/addjira.sublime-macro
│   │   ├── alfaco-atlassian.sublime-settings
│   │   ├── Default (Linux).sublime-keymap
│   │   ├── Default (Windows).sublime-keymap
│   │   ├── Default (OSX).sublime-keymap
│   │   ├── Main.sublime-menu
│   │   ├── Context.sublime-menu
│   │   ├── Side Bar.sublime-menu
│   │   ├── messages.json
│   │   ├── messages/install.txt
│   │   ├── tests/
│   │   ├── .python-version
│   │   ├── package-metadata.json
│   │   └── README.md
│   │
│   ├── AlfacoEditing/
│   │   ├── plugin.py
│   │   ├── commands/
│   │   │   ├── text_to_table.py
│   │   │   ├── select_between_markers.py
│   │   │   ├── insert_tag.py
│   │   │   ├── remove_tag.py
│   │   │   ├── date_selection.py
│   │   │   ├── show_file_name.py            ← ex-DonneNomFichierCommand
│   │   │   ├── modify_setting_from_selection.py
│   │   │   └── show_selected_input.py       ← bug nput_view corrigé
│   │   ├── snippets/alfaco-key.sublime-snippet
│   │   ├── macros/replace.sublime-macro
│   │   ├── alfaco-editing.sublime-settings
│   │   ├── Default (Linux).sublime-keymap
│   │   ├── Default (Windows).sublime-keymap
│   │   ├── Default (OSX).sublime-keymap
│   │   ├── Default.sublime-commands         ← palette : text_to_table
│   │   ├── tests/
│   │   ├── .python-version
│   │   ├── package-metadata.json
│   │   └── README.md
│   │
│   └── AlfacoCompletion/
│       ├── plugin.py
│       ├── tests/
│       ├── .python-version
│       ├── package-metadata.json
│       └── README.md
│
├── tools/                            ← infra du monorepo (jamais déployé)
│   ├── deploy.py                     ← logique link/copy/uninstall multi-OS
│   ├── new_plugin.py                 ← scaffold d'un nouveau plugin
│   └── templates/plugin/             ← squelette pour `make new-plugin`
│
├── docs/                             ← documentation utilisateur + dev (déjà existante, à mettre à jour)
│   ├── README.md
│   ├── architecture.md
│   ├── contributing.md
│   ├── deployment.md
│   ├── plugins/
│   │   ├── alfaco-lib.md
│   │   ├── alfaco-atlassian.md
│   │   ├── alfaco-editing.md
│   │   └── alfaco-completion.md
│   ├── troubleshooting.md
│   └── superpowers/specs/2026-05-08-multi-plugins-monorepo-design.md  (ce fichier)
│
├── Makefile                          ← link, install, uninstall, status, test, new-plugin, clean
├── pyproject.toml                    ← dev deps : pytest, requests-mock
├── .gitignore
├── CLAUDE.md
├── README.md                         ← réécrit pour décrire le monorepo
└── LICENSE
```

### Flux d'import inter-package

Côté lib :
```python
# plugins/AlfacoLib/config.py
class Configuration:
    def __init__(self, settings_files): ...
    def get(self, key, default=None): ...
    def set(self, key, value): ...
    def jira_auth(self): ...
    def base_url(self, version=None): ...

# plugins/AlfacoLib/atlassian_client.py
def call_rest(url, body, auth, headers, verb="GET",
              verify=True, timeout=(5, 30)): ...
```

Côté consommateur :
```python
# plugins/AlfacoAtlassian/plugin.py
import importlib
import sublime
from AlfacoLib import config as _alfacolib_config
from AlfacoLib import atlassian_client as _alfacolib_client
from AlfacoLib import io as _alfacolib_io

_LIB_MODULES = (_alfacolib_config, _alfacolib_client, _alfacolib_io)

config = None

def plugin_loaded():
    global config
    for mod in _LIB_MODULES:
        importlib.reload(mod)
    config = _alfacolib_config.Configuration([
        "alfaco-atlassian.sublime-settings",
        "Preferences.sublime-settings",
    ])

# import des classes pour découverte par Sublime
from AlfacoAtlassian.commands.create_jira_issue import CreateJiraIssueCommand
from AlfacoAtlassian.commands.select_organisation import SelectOrganisationCommand
from AlfacoAtlassian.commands.select_jira_project import SelectJiraProjectCommand
from AlfacoAtlassian.commands.open_jira_projects import OpenJiraProjectsCommand
from AlfacoAtlassian.commands.init_json_jira import InitJsonJiraCommand
from AlfacoAtlassian.commands.set_jira_project_in_snippet import SetJiraProjectInSnippetCommand
```

### Subtilités Sublime à connaître

- **Ordre de chargement alphabétique** : `AlfacoLib` < `AlfacoAtlassian` → la lib est chargée avant ses consommateurs.
- **Reload non-cascadant** : modifier la lib ne reload pas automatiquement les consommateurs. `importlib.reload()` dans `plugin_loaded()` corrige le cas où on sauvegarde un consommateur après une modif de lib.
- **Plugin host unique** (D5) : `.python-version` à `3.8` partout. Sans cela, des packages dans des hosts différents ne peuvent pas s'importer.
- **Auto-découverte** des classes `*Command` / `EventListener` : Sublime scanne le `__init__` dynamique du package, ce qui inclut les imports déclenchés depuis `plugin.py`.
- **Fusion automatique des `Main.sublime-menu`** entre packages : chaque plugin déclare sa branche, Sublime concatène. On organise donc `Tools → Alfaco → <Atlassian|Editing|...>` avec une entrée par plugin.

## Migration du code existant

### Mapping Python

| Source actuelle | Destination | Transformation |
|---|---|---|
| `AlfacoPlugins.py` (250 lignes) | éclaté entre `AlfacoAtlassian/plugin.py` + `AlfacoAtlassian/commands/*.py` + `AlfacoEditing/plugin.py` + `AlfacoEditing/commands/*.py` | Une commande = un fichier. |
| `text_to_table.py` | `AlfacoEditing/commands/text_to_table.py` | Identique. |
| `AlfacoCompletion.py` | `AlfacoCompletion/plugin.py` | Identique. |
| `modules/__init__.py` | supprimé | Le namespace `modules/` disparaît. |
| `modules/configuration.py` (`Configuration`) | `AlfacoLib/config.py` | Réécrit : attributs d'instance (pas de classe), API en snake_case (`get`, `set`, `jira_auth`, `base_url`), méthodes cassées (`setOrganisation`, `getOrganisationJiraProjects`) supprimées. |
| `modules/tools.py` | `AlfacoLib/atlassian_client.py` (REST) + `AlfacoLib/io.py` (FS) | `verify` configurable (défaut `True`), `timeout` ajouté, `os.path.join` au lieu de `\\`, exceptions remontées. |
| `modules/atlassian.py` | supprimé | Squelette vide. |

### Mapping commandes (renommages D11)

| Classe actuelle | Classe cible | Plugin |
|---|---|---|
| `OpenJiraProjectsCommand` | `OpenJiraProjectsCommand` (`print(password)` retiré) | AlfacoAtlassian |
| `GetListOrganisationCommand` | `SelectOrganisationCommand` | AlfacoAtlassian |
| `GetJiraListForOrganisationCommand` | `SelectJiraProjectCommand` | AlfacoAtlassian |
| `AppelRestApiCommand` | `CreateJiraIssueCommand` | AlfacoAtlassian |
| `SetJiraProjectInSnippetCommand` | `SetJiraProjectInSnippetCommand` | AlfacoAtlassian |
| `InitJsonJiraCommand` | `InitJsonJiraCommand` | AlfacoAtlassian |
| `DonneNomFichierCommand` | `ShowFileNameCommand` | AlfacoEditing |
| `InsertTagCommand` | `InsertTagCommand` | AlfacoEditing |
| `RemoveTagCommand` | `RemoveTagCommand` | AlfacoEditing |
| `SelectBetweenMarkersCommand` | `SelectBetweenMarkersCommand` | AlfacoEditing |
| `DateSelectionCommand` | `DateSelectionCommand` | AlfacoEditing |
| `ModifySettingFromSelectionCommand` | `ModifySettingFromSelectionCommand` | AlfacoEditing |
| `ShowSelectedInputCommand` | `ShowSelectedInputCommand` (bug `nput_view` corrigé) | AlfacoEditing |
| `TextToTableCommand` | `TextToTableCommand` | AlfacoEditing |
| `AlfacoCompletion` | `AlfacoCompletion` | AlfacoCompletion |

### Mapping ressources Sublime

| Source actuelle | Destination |
|---|---|
| `alfaco.sublime-settings` | éclaté : clés Atlassian → `AlfacoAtlassian/alfaco-atlassian.sublime-settings`, clé `alfaco_delimiter` → `AlfacoEditing/alfaco-editing.sublime-settings`. |
| `alfaco-atlassian.sublime-settings` (catalogue orgs) | fusionné dans `AlfacoAtlassian/alfaco-atlassian.sublime-settings`. |
| `Main.sublime-menu` | éclaté : branches Jira/Atlassian → `AlfacoAtlassian/`, autres → plugin concerné. |
| `Context.sublime-menu` | éclaté par domaine. |
| `Side Bar.sublime-menu` | `AlfacoAtlassian/Side Bar.sublime-menu` (deux entrées Jira-related). |
| `Default.sublime-commands` | `AlfacoEditing/Default.sublime-commands`. |
| `Default (Linux\|Windows\|OSX).sublime-keymap` | éclaté par OS dans **chaque** plugin. Bindings adaptés aux nouveaux noms de commandes. |
| `snippets/jira/*.sublime-snippet` | `AlfacoAtlassian/snippets/jira/`. |
| `snippets/confluence/*.sublime-snippet` | `AlfacoAtlassian/snippets/confluence/`. |
| `snippets/{jira,page,childPage,space}.sublime-snippet` (racine) | **supprimés** (D13, doublons). |
| `snippets/alfaco-key.sublime-snippet` | `AlfacoEditing/snippets/`. |
| `macros/addjira.sublime-macro` | `AlfacoAtlassian/macros/`. |
| `macros/replace.sublime-macro` | `AlfacoEditing/macros/`. |
| `package-metadata.json` | éclaté en un par plugin, version indépendante. |

### Bugs corrigés pendant la migration (D12)

1. `nput_view` → `input_view` (`ShowSelectedInputCommand`).
2. Login Jira codé en dur (`jlbionville@alfaco.fr`) → `config.get("jira_login")`.
3. `setSetting("organisation", "business-projects")` mutant `Preferences.sublime-settings` → `config.set()` en mémoire seulement.
4. `requests.request(..., verify=False)` → `verify=config.get("tls_verify", True)`.
5. `timeout` ajouté à toutes les requêtes (défaut `(5, 30)`).
6. `"{}\\error_api_call_…".format(...)` → `os.path.join(...)`.
7. `Configuration.setOrganisation` / `getOrganisationJiraProjects` (cassées sans `self`) → supprimées.
8. `print(jira_password)` (`OpenJiraProjectsCommand`) → retiré.
9. `snippets/jira.sublime-snippet` (duedate `"2022-02-23"`) → supprimé (gardé uniquement `snippets/jira/jira.sublime-snippet` à variables).

## Outillage

### Makefile

```makefile
# Cibles principales (toutes acceptent PLUGIN=AlfacoAtlassian pour cibler un seul plugin)

link            # Symlinks plugins/* → <Packages>/  (mode dev, modifs en direct)
install         # Copie plugins/* → <Packages>/    (mode installation propre)
uninstall       # Supprime <Packages>/Alfaco*
relink          # uninstall + link (utile après renommage)
status          # Liste les Alfaco* présents dans <Packages>/, mode (link/copy)
test            # pytest sur plugins/*/tests/ (avec stub sublime)
new-plugin      # Scaffold plugins/Alfaco<NAME> depuis tools/templates/plugin/
                # Usage: make new-plugin NAME=Git
clean           # Supprime __pycache__, .pytest_cache, *.pyc
```

### `tools/deploy.py`

Détection du dossier Sublime `Packages/` par OS, avec override `SUBLIME_PACKAGES_DIR` ou `--packages-dir=` :

| OS / Contexte | Chemin par défaut |
|---|---|
| Linux ST4 | `~/.config/sublime-text/Packages/` |
| Linux ST3 | `~/.config/sublime-text-3/Packages/` |
| macOS | `~/Library/Application Support/Sublime Text/Packages/` |
| Windows | `%APPDATA%\Sublime Text\Packages\` |
| WSL → Sublime sur Windows hôte | `/mnt/c/Users/<user>/AppData/Roaming/Sublime Text/Packages/` |

Logique de `link` :
- Linux/macOS : `os.symlink()`.
- Windows natif : tentative `os.symlink()` puis fallback **junction** (`mklink /J`) — pas de Developer Mode requis.
- WSL → Windows : forcer `install` (copie) car les symlinks WSL ne sont pas suivis par le NTFS Windows. Avertir l'utilisateur.

Exclusion lors du link/copy : `tests/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.git*`, `.python-version`*. Sinon Sublime tenterait de charger les tests comme plugins.

> *`.python-version` doit être copié, lui — il est lu par Sublime.

### Tests

- `pytest` à la racine du monorepo, configuré par `pyproject.toml` (`[tool.pytest.ini_options].testpaths = ["plugins"]`).
- Stub de `sublime` dans un `conftest.py` partagé (`sys.modules['sublime'] = MagicMock()`).
- `requests-mock` pour mocker les appels HTTP Atlassian.
- Couverture initiale ciblée sur `AlfacoLib` (logique pure). Les commandes Sublime restent peu testables sans framework dédié — `UnitTesting` reste une évolution future.

### Versioning

`package-metadata.json` par plugin, SemVer.

| Plugin | Version initiale | Justification |
|---|---|---|
| `AlfacoLib` | `0.1.0` | Nouveau package. |
| `AlfacoAtlassian` | `0.2.0` | Hérite de l'actuel `0.1.0` + breaking changes (renommage commandes, keymaps cassés). |
| `AlfacoEditing` | `0.2.0` | Idem. |
| `AlfacoCompletion` | `0.2.0` | Idem. |

Champ custom `dependencies_alfaco` dans le `package-metadata.json` des consommateurs — non lu par Sublime/Package Control, mais exploité par `tools/deploy.py` pour avertir si la lib manque au moment du `link`/`install`.

## Plan d'actions

12 étapes ordonnées, chaque étape laisse le repo dans un état fonctionnel. Le code legacy à la racine reste opérationnel jusqu'à l'étape 7 incluse.

### Phase A — Squelette (sans casser l'existant)

| # | Étape | Commit suggéré |
|---|---|---|
| 1 | Squelette monorepo (`plugins/`, `tools/`, `Makefile`, `pyproject.toml`, `tools/deploy.py`, `tools/new_plugin.py`, `tools/templates/plugin/`). | `mise en place du squelette monorepo et de l'outillage de déploiement` |
| 2 | `AlfacoLib` complet (config, client REST, io, settings, logger, tests, `.python-version`, `package-metadata.json`). | `ajout du package AlfacoLib` |
| 3 | Câblage `make test` + stub sublime + premiers tests passants. | `mise en place de pytest avec stub sublime` |

### Phase B — Migration (le legacy reste actif)

| # | Étape | Commit suggéré |
|---|---|---|
| 4 | `AlfacoEditing` complet (commandes renommées, fix `nput_view`, macro `replace`, snippet `alfaco-key`, settings, keymaps 3 OS, palette). | `migration AlfacoEditing avec corrections` |
| 5 | `AlfacoCompletion` complet. | `migration AlfacoCompletion` |
| 6 | `AlfacoAtlassian` complet (commandes renommées, fix login codé en dur + `os.path.join` + `verify` + `timeout` + `setSetting` retiré + `print(password)` retiré, snippets jira/confluence, doublons supprimés, macro `addjira`, settings, keymaps, menus, sidebar). | `migration AlfacoAtlassian avec corrections de bugs et nettoyage` |
| 7 | Validation d'intégration : `make uninstall && make link`, smoke tests manuels (palette, menus, keybindings, workflow Jira complet). | `validation d'intégration multi-plugins` |

### Phase C — Nettoyage (on coupe le legacy)

| # | Étape | Commit suggéré |
|---|---|---|
| 8 | Suppression du code racine (`AlfacoPlugins.py`, `AlfacoCompletion.py`, `text_to_table.py`, `modules/`, `macros/`, `snippets/`, `alfaco*.sublime-settings`, 3 keymaps, 3 menus, `Default.sublime-commands`, `package-metadata.json`). | `suppression du code legacy à la racine` |
| 9 | Mise à jour de `docs/` : `architecture.md`, `contributing.md`, nouveau `deployment.md`, un `docs/plugins/<nom>.md` par plugin, `troubleshooting.md` réorganisé, `CLAUDE.md` racine. | `mise à jour de la documentation pour la structure multi-plugins` |
| 10 | Réécriture du `README.md` racine (stub actuel → description monorepo, install rapide, liste des plugins). | `réécriture du README racine du monorepo` |

### Phase D — Finitions

| # | Étape | Commit suggéré |
|---|---|---|
| 11 | CI GitHub Actions minimale : `make test` sur push/PR. | `ajout d'une CI GitHub Actions pour les tests` |
| 12 | PR `refactor/multi-plugins` → `development`, tag `monorepo-v0.2.0` du dépôt après merge (les plugins individuels gardent leur version dans leur `package-metadata.json`). | (tag, pas de commit) |

## Estimation d'effort

| Phase | Étapes | Effort approximatif |
|---|---|---|
| A — Squelette | 1-3 | ~3-4 h |
| B — Migration | 4-7 | ~5-6 h |
| C — Nettoyage | 8-10 | ~2-3 h |
| D — Finitions | 11-12 | ~1 h |
| **Total** | | **~11-14 h** |

## Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| `requests` indisponible dans le plugin host de l'utilisateur. | Bloquant — la lib ne se charge pas. | Documenter dans `docs/installation.md`. À terme : déclarer `requests` comme dépendance Package Control via `dependencies.json` (hors scope de ce travail mais préparé). |
| Sublime ne reload pas correctement la lib après un `make link`. | Plugins consommateurs en erreur d'import au premier chargement. | `importlib.reload()` (D7) + redémarrage Sublime au premier déploiement (`make link` affiche un avertissement). |
| WSL ↔ Windows : symlinks cassés. | `make link` ne fonctionne pas en WSL. | `tools/deploy.py` détecte WSL, force `install` (copie), affiche un message. |
| Régression fonctionnelle non détectée par les tests (commandes Sublime peu testables). | Bug en prod. | Étape 7 dédiée à la validation manuelle (smoke tests sur tous les workflows). Liste des workflows à tester documentée dans le plan d'implémentation. |
| Renommage casse les keymaps que l'utilisateur a personnalisées. | Raccourcis cassés. | D11 assumé. La migration met à jour les 3 keymaps fournies du package ; si l'utilisateur a des bindings dans `User/`, à corriger manuellement (documenté). |
| Conflit de chargement entre legacy `Alfaco/` et nouveaux `Alfaco*/` pendant les phases A-B. | Doublons de commandes / settings. | `tools/deploy.py uninstall` en début d'étape 4 pour retirer le legacy ; ou renommage temporaire du dossier legacy. |

## Critères d'acceptation

- [ ] `make link` produit un état Sublime fonctionnel, identique au comportement actuel (workflow Jira complet validé).
- [ ] `make uninstall` retire intégralement les packages.
- [ ] `make test` passe avec ≥80% de couverture sur `AlfacoLib`.
- [ ] `make new-plugin NAME=Demo` produit un plugin minimal qui charge sans erreur dans Sublime.
- [ ] Les 9 bugs listés en migration sont fermés.
- [ ] `docs/` est à jour, sans référence au layout legacy.
- [ ] PR `refactor/multi-plugins` mergée sur `development`.

## Évolutions hors scope (préparées mais pas implémentées)

- Publication des packages sur Package Control (chaque plugin a déjà `messages.json` + `package-metadata.json`).
- Tests d'intégration headless avec `UnitTesting`.
- Plugin `AlfacoGit`, `AlfacoMarkdown` (le scaffold `make new-plugin` les supporte).
- Internationalisation des menus/messages (actuellement français uniquement).
- Migration de `requests` vers `urllib.request` (stdlib) pour supprimer la dépendance externe.

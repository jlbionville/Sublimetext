# Architecture

## Topologie

Monorepo `plugins/` contenant 4 packages Sublime Text indépendants. `AlfacoLib` est une bibliothèque sans commande utilisateur, importée par les autres plugins.

```
┌─────────────────────────────────────────────────────────────┐
│  Sublime Text 4 — dossier Packages/                          │
│                                                              │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ AlfacoLib/  │◄─┤ AlfacoAtlassian/ │  │AlfacoEditing/│   │
│  │             │  │                  │  │              │   │
│  │ • config    │  │ • commandes Jira │  │ • text_to_   │   │
│  │ • atlassian │  │ • snippets       │  │   table      │   │
│  │   _client   │  │ • settings JSON  │  │ • marqueurs  │   │
│  │ • io        │  │ • keymaps        │  │ • dates      │   │
│  │ • logger    │  │ • menus          │  │ • snippets   │   │
│  └─────────────┘  └──────────────────┘  └──────────────┘   │
│         ▲                                                    │
│         │              ┌────────────────┐                    │
│         └──────────────┤AlfacoCompletion│                    │
│                        │ • EventListener│                    │
│                        └────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

`AlfacoLib` n'expose **aucune commande utilisateur**. Les autres plugins sont autonomes côté ressources Sublime (settings, keymaps, snippets, menus).

## Structure du monorepo

```
Sublimetext/
├── plugins/                          un sous-dossier = un package Sublime déployable
│   ├── AlfacoLib/                    bibliothèque partagée
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── atlassian_client.py
│   │   ├── io.py
│   │   ├── logger.py
│   │   ├── tests/                    pytest (exclu du déploiement)
│   │   ├── .python-version           "3.8" — plugin host Sublime
│   │   ├── package-metadata.json
│   │   └── README.md
│   ├── AlfacoAtlassian/
│   │   ├── plugin.py                 entry point + plugin_loaded + importlib.reload
│   │   ├── commands/                 une commande = un fichier
│   │   ├── snippets/jira/
│   │   ├── snippets/confluence/
│   │   ├── macros/
│   │   ├── alfaco-atlassian.sublime-settings
│   │   ├── Default (Linux|Windows|OSX).sublime-keymap
│   │   ├── Main.sublime-menu, Context.sublime-menu, Side Bar.sublime-menu
│   │   ├── tests/
│   │   └── ...
│   ├── AlfacoEditing/                idem AlfacoAtlassian
│   └── AlfacoCompletion/             EventListener seul
├── tools/                            infra du monorepo (jamais déployé)
│   ├── deploy.py                     link/install/uninstall/status multi-OS
│   ├── new_plugin.py                 scaffold
│   └── templates/plugin/             template pour make new-plugin
├── docs/                             cette documentation
├── Makefile                          link/install/uninstall/status/test/new-plugin/clean
├── pyproject.toml                    pytest config + dev deps
├── conftest.py                       stub sublime/sublime_plugin pour pytest
└── README.md
```

## Cycle de vie d'un plugin

### Démarrage Sublime

1. Sublime charge les packages par ordre **alphabétique** : `AlfacoAtlassian` → `AlfacoCompletion` → `AlfacoEditing` → `AlfacoLib`.
2. **Mais l'import** de `AlfacoLib.X` depuis `AlfacoAtlassian.plugin` se fait au moment où Python évalue `from AlfacoLib import config` — au chargement de `AlfacoAtlassian.plugin`. À ce stade, `AlfacoLib` est déjà sur `sys.path` car Sublime l'a découvert. L'import marche.
3. Sublime appelle `plugin_loaded()` de chaque package après l'import.

### `plugin_loaded()` type d'un consommateur

```python
import importlib
from AlfacoLib import config as _alfacolib_config
from AlfacoLib import atlassian_client as _alfacolib_client
# ...

_LIB_MODULES = (_alfacolib_config, _alfacolib_client, ...)
config = None

def plugin_loaded():
    global config
    for mod in _LIB_MODULES:
        importlib.reload(mod)         # force le reload après modif de la lib
    config = _alfacolib_config.Configuration([
        "alfaco-<nom>.sublime-settings",
        "Preferences.sublime-settings",
    ])
```

Le `importlib.reload()` est crucial pendant le développement : Sublime ne reload pas automatiquement les packages dépendants quand on modifie `AlfacoLib`. En sauvant le `plugin.py` du consommateur, le reload de la lib est forcé.

### Auto-découverte des commandes

Sublime scanne le namespace de chaque package et instancie automatiquement toute classe qui hérite de `sublime_plugin.TextCommand` / `WindowCommand` / `EventListener`. Pour qu'elles soient découvertes, on les **importe** dans `plugin.py` :

```python
from AlfacoEditing.commands.text_to_table import TextToTableCommand  # noqa: F401
from AlfacoEditing.commands.insert_tag import InsertTagCommand  # noqa: F401
# ...
```

Le `noqa: F401` indique au linter de ne pas signaler l'import inutilisé : il l'est, par effet de bord (déclencher l'auto-découverte).

## Modèle de données

### `Configuration` empilée

`AlfacoLib.config.Configuration` lit les clés dans cet ordre :

1. **Runtime** (`set()` en mémoire pendant la session — perdu au redémarrage).
2. **Settings layers** (les `.sublime-settings` passés au constructeur, dans l'ordre).
3. **Default** passé à `get(key, default=...)`.

Aucun effet de bord sur `Preferences.sublime-settings` (contrairement au legacy qui faisait `setSetting("organisation", ...)` au démarrage).

### Catalogue Atlassian

Le bloc `atlassian.organisations` du settings est un dictionnaire `{nom_libellé: {url_key, jira, confluence}}`. La commande `select_organisation` lit ce catalogue et propose un popup. La sélection met à jour `default_organisation` en runtime.

## Subtilités Sublime

- **Plugin host Python 3.8** uniquement (`.python-version` à `3.8` dans chaque plugin). Tous les packages qui s'importent mutuellement doivent partager le même host.
- **Fusion automatique des `Main.sublime-menu`** entre packages : chaque plugin déclare sa branche, Sublime concatène. La hiérarchie cible est `Tools → Alfaco → <Atlassian|Editing|...>`.
- **Macros et keymaps** référencent les snippets via `Packages/<NomPackage>/snippets/...`. Les chemins ont été mis à jour lors de la migration depuis `Packages/User/...` du legacy.
- **Headers POST** : `CreateJiraIssueCommand` ne les écrase plus à chaque appel — la `Configuration` les fournit via `cfg.get("headers", default)`.

## Flux d'un appel REST Atlassian

```
Utilisateur invoque create_jira_issue (Alt+J ou palette)
    └─> CreateJiraIssueCommand.run(edit)
        ├─ contenu = self.view.substr(Region(0, size))   # buffer entier
        ├─ cfg = AlfacoAtlassian.plugin.config
        ├─ url = cfg.base_url() + "issue/"
        ├─ AlfacoLib.atlassian_client.call_rest(
        │       url, body=contenu, auth=cfg.jira_auth(),
        │       headers=cfg.get("headers"),
        │       verb="POST",
        │       verify=cfg.get("tls_verify", True),
        │       timeout=(5, 30))
        │   └─> requests.request(...)
        │       └─> POST https://<org>.atlassian.net/rest/api/<v>/issue/
        ├─ new_view.run_command("insert", {"characters": response.text})
        ├─ save_file(response.text, build_response_path(folder, ts))
        └─ save_file(contenu, build_payload_path(folder, jira_key))
```

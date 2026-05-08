# Guide du contributeur

## Conventions

- **Langue** : code, commentaires, captions de menus, libellés de commandes en **français**. Documentation idem.
- **Encoding** : tous les fichiers `.py` commencent par `# -*- coding: utf-8 -*-`.
- **Style Python** : indentation 4 espaces, snake_case fonctions, PascalCase classes, suffixe `Command` pour sous-classes Sublime.
- **Plugin host** : Python 3.8 uniquement (`.python-version` à `3.8` dans chaque plugin).
- **Une commande = un fichier** dans `plugins/<Plugin>/commands/`.

## Cycle de développement

1. Cloner le dépôt n'importe où (pas besoin d'être dans `Packages/`).
2. `make link` (Linux/macOS) ou `make install` (WSL/Windows) pour déployer dans `<Packages>/`.
3. Modifier un fichier `.py` ; Sublime recharge à la sauvegarde.
4. Console Sublime (`` Ctrl+` ``) pour les `print` et exceptions.
5. `make test` pour la suite pytest hors-Sublime.

## Ajouter un nouveau plugin

```bash
make new-plugin NAME=Git
```

Crée `plugins/AlfacoGit/` à partir de `tools/templates/plugin/`. Le scaffold injecte :
- `plugin.py` avec `plugin_loaded()` et boilerplate `importlib.reload(_alfacolib_config)`.
- `commands/__init__.py` vide.
- `tests/conftest.py` (stub sublime).
- `.python-version` = `3.8`.
- `package-metadata.json` versionné `0.2.0`.
- `README.md`.

Compléter ensuite : settings, keymaps (3 OS), menus, snippets selon les besoins du plugin.

## Ajouter une commande à un plugin existant

1. Créer le fichier dans `plugins/<Plugin>/commands/<nom_snake>.py` :

```python
# -*- coding: utf-8 -*-
"""<Description>"""
import sublime_plugin


class MaCommandeCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        ...
```

2. Enregistrer la classe dans `plugin.py` :

```python
from <Plugin>.commands.ma_commande import MaCommandeCommand  # noqa: E402, F401
```

3. (Optionnel) Ajouter le binding dans **les 3 keymaps OS** (Linux/Windows/OSX).
4. (Optionnel) Ajouter une entrée dans `Main.sublime-menu`, `Default.sublime-commands` (palette), etc.
5. Si la commande utilise la lib : utiliser `from AlfacoLib.X import Y`.
6. Si la commande utilise la config du plugin : `from <Plugin> import plugin as _<plugin>; _<plugin>.config.get("ma_clé")`.

## Tests

Aucun framework de test Sublime intégré. On teste **hors Sublime** via pytest et le stub `conftest.py` racine.

```bash
make test                              # toute la suite
pytest plugins/AlfacoLib/tests/        # un seul plugin
pytest -k "test_my_function"           # filtre par nom
```

Pour mocker des appels HTTP : `requests-mock`.

```python
def test_call_rest_post():
    with requests_mock.Mocker() as m:
        m.post("https://...", json={"ok": True}, status_code=201)
        result = call_rest(...)
    assert result.status_code == 201
```

Les commandes Sublime (`*Command`) ne sont pas testables hors Sublime sans framework dédié comme `UnitTesting`. On extrait la logique pure dans des fonctions / classes testables et on couvre via `pytest`.

## Workflow git

- Branche par défaut : `main`.
- Branche de travail : `development`.
- Branches de feature : `refactor/...`, `feat/...`, `fix/...`.
- Messages en français, à l'impératif court.

## Architecture cible

Voir [architecture.md](architecture.md). Les principes-clés :
- `AlfacoLib` ne contient AUCUNE commande utilisateur.
- Chaque plugin a son `plugin.py` qui boilerplate `importlib.reload()` les modules de lib.
- Les imports `from <Plugin>.commands.X import YCommand` dans `plugin.py` déclenchent l'auto-découverte par Sublime.

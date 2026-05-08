# Guide du contributeur

## Conventions

- **Langue** : code, commentaires, captions de menus, libellés de commandes en **français**. La documentation suit la même règle.
- **Encoding** : tous les fichiers `.py` commencent par `# -*- coding: utf-8 -*-` (ajouté dans le commit `1d4c57a`).
- **Style Python** : pas de `pyproject.toml`, pas de `pre-commit`, pas de linter configuré. Suivre PEP 8 par défaut, indentation 4 espaces, snake_case pour les fonctions, PascalCase pour les classes, suffixe `Command` pour les sous-classes Sublime.

## Cycle de développement

1. Cloner le dépôt directement dans `Packages/Alfaco/` ou via lien symbolique (voir [installation.md](installation.md#installer-le-package)).
2. Modifier un fichier `.py` ; à la sauvegarde Sublime recharge automatiquement le plugin et rappelle `plugin_loaded()`.
3. Ouvrir la console Sublime (`` Ctrl+` ``) pour voir les `print()` et les exceptions.
4. Tester manuellement la commande via la palette (`Ctrl+Shift+P` → taper le nom snake_case) ou son raccourci.
5. Pas de tests automatisés. Quelques pistes pour en ajouter : voir [Tester](#tester).

## Ajouter une nouvelle commande Jira/Atlassian

### 1. Créer la classe dans `AlfacoPlugins.py`

```python
class MaNouvelleCommandeCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        # 1. Lire la configuration partagée
        url = configuration.getBaseUrlForRESTApi() + "endpoint/cible/"
        configu = {
            "url":     url,
            "headers": configuration.getKeyValue("headers"),
            "auth":    configuration.getJiraAuthorisation()
        }
        # 2. Préparer le payload (depuis le buffer ou args)
        contenu = self.view.substr(sublime.Region(0, self.view.size()))
        # 3. Appeler l'API
        reponse = callApiRest(contenu, configu, http_verb="POST")
        # 4. Afficher la réponse
        new_view = self.view.window().new_file()
        new_view.run_command("insert", {"characters": reponse})
```

### 2. Convention de nommage

Sublime convertit automatiquement `MaNouvelleCommandeCommand` → `ma_nouvelle_commande`.

### 3. Enregistrer la commande

Selon les surfaces visées, modifier :

| Cible | Fichier | Exemple |
|---|---|---|
| Palette de commandes | `Default.sublime-commands` | `{"caption": "Alfaco: ma commande", "command": "ma_nouvelle_commande"}` |
| Menu Tools | `Main.sublime-menu` | Ajouter une entrée dans `tools → alfaco → children`. |
| Menu contextuel | `Context.sublime-menu` | Ajouter dans `Alfaco` ou `Jira`. |
| Sidebar | `Side Bar.sublime-menu` | Idem. |
| Raccourci clavier | **Les trois** keymaps | Voir [usage.md — Raccourcis clavier](usage.md#raccourcis-clavier). |

### 4. Si la commande lit/écrit un setting

- Lire via `getSetting("ma_cle")` (qui empile les trois fichiers — voir [configuration.md](configuration.md#ordre-de-résolution)).
- Si la valeur est dynamique (choisie en session), passer par `configuration.setKeyValue("ma_cle", val)` / `getKeyValue`.
- Si la valeur doit être persistée globalement, utiliser `setSetting()` (mais c'est intrusif : ça mute `Preferences.sublime-settings`).

### 5. Documenter

- Ajouter une ligne dans [usage.md → Référence des commandes](usage.md#référence-des-commandes).
- Si la commande a un raccourci, mettre à jour la table des raccourcis.
- Si elle lit une nouvelle clé settings, ajouter dans [configuration.md](configuration.md).

## Ajouter un snippet

1. Créer un fichier `.sublime-snippet` sous `snippets/` (sous-dossier `jira/` ou `confluence/` si pertinent).
2. Structure XML :
   ```xml
   <snippet>
       <content><![CDATA[
   {
       "field": "${1:valeur_par_defaut}",
       "autre": "${2}"
   }
       ]]></content>
       <tabTrigger>montrigger</tabTrigger>
       <!-- <scope>source.json</scope>  optionnel -->
   </snippet>
   ```
3. Variables custom (passées via `insert_snippet`) sont injectables : `${maVariable}`. Voir `snippets/jira/jira.sublime-snippet` pour `${jira_key}`, `${duedate}`, `${description}`.
4. Tester en saisissant `montrigger` puis `Tab` dans un buffer JSON.

## Ajouter un keybinding

Toujours mettre à jour les **trois** fichiers keymap :

- `Default (Linux).sublime-keymap`
- `Default (Windows).sublime-keymap`
- `Default (OSX).sublime-keymap`

Sur macOS, remplacer `ctrl+alt+...` par `ctrl+super+...` (Cmd) pour rester ergonomique.

```json
{
    "keys": ["ctrl+alt+x"],
    "command": "ma_nouvelle_commande",
    "args": { "param": "valeur" },
    "context": [
        { "key": "selection_empty", "operator": "equal", "operand": false }
    ]
}
```

## Workflow git

Le dépôt suit un workflow simple :

- Branche par défaut : `main`.
- Branche de travail courante : `development`.
- Messages de commit en français, à l'impératif ou descriptif court (cf. `git log`) : « ajout de … », « correction bug : … », « refactorisation … ». Un commit = un changement focalisé.
- Pas de PR template, pas de CI configurée actuellement.

### Exemples de bons messages (issus de l'historique)

```
correction bug : indication du verbe HTTP
ajout d'une variable pour la date de la jira
refactorisation des settings
utilisation de l'object configuration
```

## Tester

Aucun framework de test n'est configuré. Pistes recommandées si on veut industrialiser :

- **Tests unitaires hors Sublime** : extraire la logique testable de `modules/tools.py` (notamment `getUrlToGetJiraProjects`) dans des fonctions pures, mocker `requests` avec `responses` ou `requests-mock`, lancer via `pytest` dans un venv standard.
- **Tests d'intégration dans Sublime** : utiliser le package `UnitTesting` (https://github.com/SublimeText/UnitTesting) qui pilote Sublime en CI.
- **Smoke test manuel** : checklist dans une PR — créer une issue dans un projet de test, supprimer après.

## Dette technique connue

Voir [troubleshooting.md](troubleshooting.md) pour la liste détaillée. Les chantiers prioritaires :

1. Déclarer `requests` comme dépendance Package Control (`dependencies.json`).
2. Retirer le login codé en dur dans `plugin_loaded()` au profit de `getSetting("jira_login")`.
3. Conditionner `verify=False` via une clé de settings.
4. Ajouter un `timeout` aux appels `requests`.
5. Réparer ou supprimer `Configuration.setOrganisation` / `getOrganisationJiraProjects`.
6. Corriger le typo `nput_view` dans `ShowSelectedInputCommand`.
7. Fusionner les snippets dupliqués entre `snippets/` et `snippets/{jira,confluence}/`.
8. Remplir le `README.md` (sections actuellement vides).
9. Aligner les keymaps des trois OS.

## Architecture cible (suggestions)

- Déplacer chaque commande dans son propre module (`commands/jira_create.py`, `commands/jira_select.py`, `commands/editing.py`) et faire de `AlfacoPlugins.py` un index d'imports.
- Remplacer la `Configuration` par un module fonctionnel (`config.get(key)`, `config.set(key, value)`) avec persistance optionnelle.
- Extraire un client HTTP `AtlassianClient` (méthodes `get_projects()`, `create_issue()`, `create_page()`) qui isole `requests` et permet d'écrire des tests sans Sublime.

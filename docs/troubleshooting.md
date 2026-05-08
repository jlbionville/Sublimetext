# Troubleshooting

## Bugs résolus pendant la migration monorepo

Les bugs suivants étaient documentés dans le legacy et sont **fixés** dans cette structure :

| Bug | Plugin / Fichier | Statut |
|---|---|---|
| Typo `nput_view` (NameError dans `ShowSelectedInputCommand`) | AlfacoEditing | Résolu |
| Login Jira codé en dur (`jlbionville@alfaco.fr`) | AlfacoAtlassian | Résolu — lit `jira_login` |
| `setSetting("organisation", ...)` mutait Preferences au démarrage | AlfacoAtlassian/plugin.py | Résolu — `config.set()` runtime |
| `verify=False` codé en dur | AlfacoLib/atlassian_client | Résolu — `tls_verify` configurable |
| Pas de timeout HTTP (UI bloque indéfiniment) | AlfacoLib/atlassian_client | Résolu — `(5, 30)` par défaut |
| `\\` Windows codés en dur (`H:\\Mon Drive\\jira\\...`) | AlfacoLib/io | Résolu — `pathlib.Path` partout |
| `Configuration.setOrganisation` / `getOrganisationJiraProjects` cassés (manque `self`) | AlfacoLib/config | Supprimés — Configuration réécrite |
| `print(jira_password)` dans console | AlfacoAtlassian/open_jira_projects | Résolu — masqué |
| Snippet `snippets/jira.sublime-snippet` avec `duedate: "2022-02-23"` | (legacy) | Résolu — supprimé, seul `snippets/jira/jira.sublime-snippet` à variables est conservé |
| Snippets en doublon entre `snippets/` et `snippets/{jira,confluence}/` | (legacy) | Résolu — versions racine supprimées |
| Headers HTTP réécrits dans `create_jira_issue` (perte du `charset=utf-8`) | AlfacoAtlassian/create_jira_issue | Résolu — préservés via `cfg.get("headers")` |

## Erreurs spécifiques au monorepo

### `ImportError: No module named 'AlfacoLib'`

Les autres plugins importent `AlfacoLib`. Si la lib n'est pas déployée, l'import échoue.

**Diagnostic** :
```bash
make status
```

Si `AlfacoLib` est `absent` : `make link PLUGIN=AlfacoLib` puis redémarrer Sublime.

### Plugin host différent

Si un plugin a `.python-version: 3.3` au lieu de `3.8`, il est chargé dans un autre interpréteur Python qui ne voit pas `AlfacoLib`.

**Vérification** : `cat plugins/*/`.python-version` — doit afficher `3.8` partout.

### WSL : symlinks NTFS qui ne marchent pas

`make link` détecte WSL et force `make install` (copie). Si tu vois quand même des "broken symlinks" dans `<Packages>/Alfaco*` :

```bash
make uninstall && make install
```

### Username Windows ≠ username WSL

Symptôme : `make link` plante avec `Profil Windows '<user>' introuvable sous /mnt/c/Users/`.

**Fix** : poser `SUBLIME_PACKAGES_DIR` :
```bash
export SUBLIME_PACKAGES_DIR='/mnt/c/Users/Jean/AppData/Roaming/Sublime Text/Packages'
make install
```

### Modifications de `AlfacoLib` non prises en compte

Sublime ne reload pas automatiquement les consommateurs d'un package modifié. Le `importlib.reload()` dans `plugin_loaded()` corrige ça **quand le consommateur est lui-même rechargé** (sauvegarde d'un de ses `.py`).

**Fix manuel** : sauvegarder un fichier `.py` du plugin consommateur (par exemple `plugins/AlfacoAtlassian/plugin.py`) après modif de `AlfacoLib/*.py`.

## Diagnostic des erreurs Atlassian

### `401 Unauthorized`

- Vérifier `jira_login` (et que ce n'est plus l'email codé en dur du legacy).
- Vérifier que `jira_password` est bien un **token API** (pas le mot de passe du compte).
- Vérifier `default_organisation` après `select_organisation` (`make` ne montre pas, mais le log debug oui — activer `"debug": true`).

### `404 Not Found` sur `/issue/`

- `api_rest_version` = `"2"` ou `"3"` ?
- API v3 attend `description` au format Atlassian Document Format. Si l'erreur persiste : passer à `"2"`.

### `400 Bad Request` à la création

- `project.key` existe ? (`select_jira_project` doit avoir réussi avant.)
- `issuetype.name` = `Task` ou `Tâche` selon la langue du projet.
- Le payload doit être encapsulé `{"fields": {...}}` — vérifier le snippet utilisé.

### Le buffer reste bloqué

Plus possible depuis l'ajout du `timeout=(5, 30)`. Si ça arrive : vérifier que `AlfacoLib/atlassian_client.py` contient bien `timeout=` dans les appels `requests.request`.

## Checklist rapide

```
□ La console Sublime (Ctrl+`) affiche-t-elle un Traceback ?
□ make status — tous les plugins sont link/copy ? (pas absent)
□ requests est-il importable ? Console : import requests
□ jira_password est-il défini dans User/alfaco-atlassian.sublime-settings ?
□ default_organisation est-il posé après Select Organisation ?
□ project_key est-il posé après Select Jira project ?
□ path_json_files_folder existe-t-il et est-il writable ?
□ api_rest_version cohérent avec le format du payload ?
□ Le buffer envoyé est-il un JSON valide ?
```

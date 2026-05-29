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

### `Package Control: Removing N orphaned packages...` au démarrage

Symptôme : les 4 plugins disparaissent de `Packages/` après chaque redémarrage. PC considère orphelin tout package contenant un `package-metadata.json` (marqueur « géré par PC ») mais non listé dans `installed_packages`.

**Fix** : depuis la v0.3.0, `tools/deploy.py` exclut `package-metadata.json` du déploiement, donc PC ne reconnaît plus nos plugins comme « gérés par lui » et n'y touche pas. Refaire `make uninstall && make install` pour purger d'anciens déploiements qui contenaient encore le fichier marqueur.

Vérification post-fix :

```bash
find "$SUBLIME_PACKAGES_DIR"/Alfaco* -name package-metadata.json
# doit être vide
```

L'ancien contournement (ajouter les 4 noms à `installed_packages`) reste valide mais devient inutile.

### `ModuleNotFoundError: No module named 'requests'`

Plus possible : `AlfacoLib.atlassian_client` n'utilise plus `requests` (remplacé par `urllib` stdlib). Si tu vois encore cette erreur : tu as un déploiement obsolète, refais `make uninstall && make install` puis redémarre Sublime.

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

### Conflit de raccourci `Ctrl+Alt+M` entre plugins (Windows) — résolu

**Résolu** : `init_markdown_jira` (AlfacoAtlassian) est passé sur `Ctrl+M` (contexte Markdown uniquement), donc `Ctrl+Alt+M` n'est plus utilisé que par `modify_setting_from_selection` (AlfacoEditing). Plus de collision.

La leçon générale reste valable : les keymaps de tous les packages sont fusionnées et, pour une même touche **sans contexte distinctif**, le package chargé en dernier (ordre alphabétique) l'emporte. Pour cohabiter sur une même touche, ajouter un `context` (comme le selector Markdown de `Ctrl+M`) ou choisir des touches distinctes. Vérifier la liaison résolue via `Preferences → Key Bindings`.

## Diagnostic des erreurs Atlassian

### `401 Unauthorized`

- Vérifier `jira_login` (et que ce n'est plus l'email codé en dur du legacy).
- Vérifier que `jira_password` est bien un **token API** (pas le mot de passe du compte).
- Vérifier `default_organisation` après `select_organisation` (`make` ne montre pas, mais le log debug oui — activer `"debug": true`).

### `404 Not Found` sur `/issue/`

- `api_rest_version` = `"2"` ou `"3"` ?

### `400 Bad Request` : « description n'est pas un contenu ADF valide » (API v3)

Plus possible depuis la v0.4.0 : `create_jira_issue` enveloppe automatiquement les descriptions plain-string en Atlassian Document Format (`{type:"doc", version:1, content:[...]}`) quand `api_rest_version` vaut `"3"`. Idempotent : si le buffer contient déjà une description ADF (dict), elle est laissée intacte. Sépare en paragraphes sur les doubles-newlines.

Si le 400 persiste, vérifier que `_json.loads(buffer)` réussit (le buffer doit être un JSON valide avant POST — sinon `create_jira_issue` montre un `error_message` explicite).

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

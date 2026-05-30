# Spec — Sélecteur de type d'issue → buffer Markdown (AlfacoAtlassian)

**Date** : 2026-05-30
**Statut** : validé (brainstorming)
**Branche** : `feat/jira-issue-type-selector`

## Problème

Aujourd'hui, le flux de création Markdown (`init_markdown_jira` → `create_jira_from_markdown`)
ouvre un buffer avec un champ `# Type` libre que l'utilisateur saisit à la main. Rien ne
garantit que le type saisi existe dans le projet courant, et l'utilisateur doit connaître
par cœur les types disponibles.

On veut un **menu** (popup) listant les types d'issues réellement supportés par le projet
courant, récupérés live depuis Jira. Sélectionner un type ouvre un buffer Markdown
pré-rempli avec ce type, prêt à éditer puis à POSTer (flux existant inchangé).

## Décisions (issues du brainstorming)

| Sujet | Décision |
|---|---|
| Contenu du menu | Les **types d'issues** du projet courant (pas les tickets existants). |
| Action à la sélection | **Ouvrir un buffer Markdown** pré-rempli avec le type (flux init existant). |
| Intégration | **Nouvelle commande dédiée** ; `Ctrl+M` (`init_markdown_jira`) inchangé. |
| Sous-tâches | **Tous les types listés**, y compris les `subtask`. |
| Raccourci | `Ctrl+J Ctrl+T` / `Cmd+J Cmd+T` (famille `Ctrl+J`, « avec Ctrl = choisir »). |
| `# Organisation` | Pré-rempli comme aujourd'hui (`default_organisation`). |

## Données Jira (vérifiées live)

`GET /rest/api/3/project/{projectIdOrKey}?expand=issueTypes` renvoie un objet projet
contenant :

```json
{
  "key": "GDQ",
  "issueTypes": [
    { "id": "10105", "name": "Tâche",      "subtask": false, "hierarchyLevel": 0 },
    { "id": "10106", "name": "Sous-tâche", "subtask": true,  "hierarchyLevel": -1 },
    { "id": "10179", "name": "Story",      "subtask": false, "hierarchyLevel": 0 },
    { "id": "10180", "name": "Tâche",      "subtask": false, "hierarchyLevel": 0 },
    { "id": "10181", "name": "Epic",       "subtask": false, "hierarchyLevel": 1 }
  ]
}
```

**Constat important** : un même **nom** peut apparaître plusieurs fois avec des `id`
différents (ici « Tâche » ×2). Comme la création Markdown référence le type **par nom**
(`fields.issuetype.name`), on **déduplique par nom** dans le popup — l'`id` n'est pas
nécessaire.

## Architecture

### 1. `AlfacoLib/atlassian_client.py` — helper pur (testable hors-Sublime)

```python
def parse_issue_type_names(data):
    """Extrait les noms de types d'un GET /project/{key}?expand=issueTypes.

    `data` est l'objet projet décodé (dict) avec une clé `issueTypes` (liste).
    Tolère aussi une liste de types passée directement.
    Retourne la liste des noms, dédupliquée (premier vu gagné), ordre préservé.
    Inclut les types subtask. Ignore les entrées sans `name`.
    """
```

Pur (pas de dépendance `sublime`) → testé comme `list_projects`.

### 2. `AlfacoAtlassian/commands/select_jira_issue_type.py` (NOUVEAU)

`SelectJiraIssueTypeCommand(sublime_plugin.TextCommand)` :

1. `cfg = plugin.config` ; lire `project_key`. Si vide →
   `sublime.error_message(...)` invitant à lancer `select_jira_project` d'abord, puis
   `return`.
2. Vérifier `jira_auth()` (login/password) comme `select_jira_project`.
3. `url = cfg.base_url() + "project/" + project_key + "?expand=issueTypes"`.
4. `call_rest(... verb="GET" ...)` avec mêmes garde-fous que `select_jira_project` :
   `URLError/socket.timeout`, status ≠ 200, JSON invalide → `error_message` explicite + log.
5. `names = parse_issue_type_names(response.json())`. Si vide → `message_dialog` explicite.
6. `self._items = names` ; `self.view.show_popup_menu(self._items, self._on_done)`.
7. `_on_done(index)` : si `-1` → log annulation ; sinon
   `self.view.run_command("init_markdown_jira", {"type": self._items[index]})`.

### 3. `init_markdown_jira.py` + snippet

État actuel du snippet : le titre et la valeur sont sur deux lignes, la valeur étant
`Task` en dur :

```
# Type
Task
```

- Snippet `snippets/jira/jira-markdown.sublime-snippet` : remplacer `Task` par `${type}`
  (nouvelle variable de snippet).
- `init_markdown_jira.py` : `args.setdefault("type", "Task")` (avant `insert_snippet`).
  Défaut `"Task"` → comportement **inchangé** quand `init_markdown_jira` est appelé sans
  `type` (Ctrl+M actuel). La commande de sélection passe le nom choisi.

### 4. Intégration UI

- `plugin.py` : `from AlfacoAtlassian.commands.select_jira_issue_type import SelectJiraIssueTypeCommand  # noqa: F401`.
- `Context.sublime-menu` : entrée `{ "caption": "créer issue (choisir le type)", "command": "select_jira_issue_type" }`.
- `Main.sublime-menu` : entrée `{ "caption": "Créer issue (choisir le type)", "command": "select_jira_issue_type" }` sous `Tools → Alfaco → Atlassian`.
- Keymaps (`Default (Linux/Windows/OSX).sublime-keymap`) :
  - Linux/Windows : `{ "keys": ["ctrl+j", "ctrl+t"], "command": "select_jira_issue_type" }`
  - OSX : `{ "keys": ["super+j", "super+t"], "command": "select_jira_issue_type" }`

## Flux utilisateur

1. `select_organisation` (pose `default_organisation`).
2. `select_jira_project` (pose `project_key`).
3. `Ctrl+J Ctrl+T` → popup des types du projet → sélection.
4. Buffer Markdown ouvert avec `# Type <choisi>`, `# Organisation <courante>`, dates auto.
5. Édition (summary, description…), puis `Alt+M` → `create_jira_from_markdown` POST (existant).

## Tests (TDD, hors-Sublime)

`plugins/AlfacoLib/tests/test_atlassian_client.py` (nouveau ou existant) —
`parse_issue_type_names` :

- extrait les noms depuis un objet projet `{"issueTypes": [...]}` ;
- **déduplique les noms en doublon** (cas « Tâche » ×2 → une seule entrée) en préservant
  l'ordre ;
- inclut les types `subtask` ;
- tolère une liste de types passée directement ;
- `issueTypes` absent/vide → `[]` ;
- entrées sans `name` ignorées.

Les `*Command` ne sont pas testables hors-Sublime (déjà documenté) : la logique testée est
concentrée dans `parse_issue_type_names`.

## Gestion d'erreurs

| Cas | Comportement |
|---|---|
| `project_key` vide | `error_message` : lancer `select_jira_project` d'abord. |
| login/token manquant | `error_message` (réutilise le pattern `select_jira_project`). |
| Erreur réseau / timeout | `error_message` + log. |
| HTTP ≠ 200 | `error_message` avec status + extrait corps. |
| JSON invalide | `error_message`. |
| 0 type retourné | `message_dialog` explicite. |

## Hors périmètre (YAGNI)

- Pas de liste des **tickets existants** (autre besoin).
- Pas de création directe sans buffer (on passe toujours par le buffer Markdown).
- Pas d'icônes de type dans le popup (`show_popup_menu` ne les supporte pas).
- Pas de gestion du parent pour les subtasks (listées mais leur POST peut échouer faute de
  parent — comportement assumé, cf. décision « tout lister »).
- Pas de pagination (les types d'un projet tiennent largement dans une réponse).

## Documentation à mettre à jour

- `docs/plugins/alfaco-atlassian.md` : commande, raccourci, workflow.
- `docs/usage.md` : index des commandes + workflow Jira.
- `CLAUDE.md` : si un apprentissage transverse émerge (sinon non).

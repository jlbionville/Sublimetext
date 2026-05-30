# Spec — Créer une issue sous un parent (Epic/Story)

**Date** : 2026-05-30
**Statut** : validé (brainstorming)
**Branche** : `feat/jira-create-under-parent`

## Problème

Le flux de création Markdown (`init_markdown_jira` → `create_jira_from_markdown`) crée des
issues « à plat ». On veut pouvoir créer une issue **rattachée à un parent** (une Epic ou
une Story).

Sur le Jira Cloud de l'instance (`my-personal-projects`), le rattachement à une Epic comme
à une Story passe par le **même champ `parent`** :
`{"fields": {"parent": {"key": "MMPO-2"}}}`. Une seule mécanique couvre les deux cas
(vérifié live : `getJiraIssue`/`search` exposent Epic et Story au même niveau de hiérarchie
parent).

## Périmètre

Ce spec couvre **uniquement la création sous un parent**. Le re-parentage de tickets
**existants** (déplacer un ticket déjà créé sous une Epic/Story via `PUT /issue/{KEY}`) est
un sous-projet distinct, traité séparément ensuite (sous-projet #2).

## Décisions (brainstorming)

| Sujet | Décision |
|---|---|
| Désignation du parent | Champ `# Parent` dans le template **+** commande popup qui le remplit. |
| Périmètre du popup | **Configurable** via `jira_parent_types` (défaut `["Epic", "Story"]`). |
| Priorité Markdown vs popup | **Markdown prioritaire** : `# Parent` du buffer fait foi au POST ; le popup ne fait que pré-remplir/mettre à jour cette section. |
| Insertion popup | Le popup **remplit la section `# Parent`** du buffer courant (cherche la ligne `# Parent`, écrit la clé en dessous ; si absente, ajoute la section avant `# Description`). |
| Raccourci popup | `Ctrl+J Ctrl+R` / `Cmd+J Cmd+R` (R = paRent ; `Ctrl+J Ctrl+T` pris par Type). |

## Données Jira (vérifiées live)

`search` JQL `project = "<KEY>" AND issuetype in (Epic, Story) ORDER BY created DESC`
renvoie des issues avec `key`, `fields.summary`, `fields.issuetype.name`. Exemple (projet
MMPO) : `MMPO-8 Story`, `MMPO-6 Epic`, `MMPO-2 Epic`…

POST de création avec parent (API v3) :
```json
{ "fields": { "summary": "...", "parent": { "key": "MMPO-2" }, "...": "..." } }
```

## Architecture

### 1. `AlfacoLib/markdown_to_adf.py` — champ `# Parent` (logique pure, testée)

- `KNOWN_FIELDS` : ajouter `"Parent"` (sinon `_split_fields` lève « champ inconnu »).
  Ordre proposé : `… "Labels", "Parent", "Startdate", "Duedate", "Description"`.
- `parse_markdown_jira_template` : après le bloc `startdate`, lire
  `parent = (fields_md.get("Parent") or "").strip()` ; si `parent` →
  `fields["parent"] = {"key": parent}`. Si vide/absent → ne pas ajouter la clé
  (rétro-compatible : les templates sans `# Parent` produisent le même payload qu'avant).
- Pas de fallback config (un parent par défaut n'a pas de sens).

### 2. `AlfacoLib/atlassian_client.py` — helper pur `parse_parent_choices`

```python
def parse_parent_choices(data):
    """Extrait les parents candidats d'une réponse Jira `search`.

    `data` est l'objet décodé du `GET .../search?jql=...`. Sur l'API moderne la
    forme est `{"issues": [{"key", "fields": {"summary", "issuetype": {"name"}}}]}`.
    Retourne une liste de tuples `(key, label)` où
    `label = "KEY — résumé (Type)"`, dans l'ordre de la réponse.
    Ignore les entrées sans `key`. Retourne `[]` si vide/mal formé.
    """
```
Pur, testé hors-Sublime (comme `parse_issue_type_names`). Retourne des tuples pour que la
commande affiche `label` dans le popup mais conserve `key` pour l'insertion.

### 3. `AlfacoAtlassian/commands/select_jira_parent.py` (NOUVEAU)

`SelectJiraParentCommand(sublime_plugin.TextCommand)` :
1. lire `project_key` ; si vide → `error_message` (lancer `select_jira_project` d'abord).
2. vérifier `jira_auth()` (mêmes gardes que `select_jira_project`).
3. `types = cfg.get("jira_parent_types", ["Epic", "Story"])` ; construire la clause
   `issuetype in (...)` en **quotant chaque type** (gère les espaces, ex. « Flux de travail ») :
   `", ".join('"%s"' % t for t in types)`.
4. `jql = 'project = "%s" AND issuetype in (%s) ORDER BY created DESC' % (project_key, clause)`.
5. URL : `cfg.base_url() + "search?jql=" + urllib.parse.quote(jql)` (encoder la JQL).
   - ⚠️ À vérifier à l'implémentation : l'endpoint classique `GET /search?jql=` existe en
     API v2 et v3. Atlassian migre vers `GET /search/jql` sur les versions récentes ; si la
     validation manuelle renvoie un 410/404, basculer sur `search/jql` (même forme de
     réponse `{"issues": [...]}`). Garde-fou HTTP déjà prévu → message explicite.
6. `call_rest(... verb="GET" ...)` avec garde-fous réseau/HTTP/JSON identiques à
   `select_jira_project`.
7. `choices = parse_parent_choices(response.json())`. Si vide → `message_dialog` explicite.
8. `self._choices = choices` ; `show_popup_menu([label for _, label in choices], self._on_done)`.
9. `_on_done(index)` : si `-1` → log annulation ; sinon
   `key = self._choices[index][0]` puis `self.view.run_command("set_markdown_parent", {"key": key})`.

### 4. Commande d'édition `set_markdown_parent` (même fichier ou dédié)

`SetMarkdownParentCommand(sublime_plugin.TextCommand)` — applique l'édition au **buffer
courant** (séparée car `_on_done` n'a pas d'`edit` token) :
- chercher la ligne `# Parent` (regex `^#\s+Parent\s*$`).
- si trouvée : remplacer la **ligne suivante** par `key` (ou l'insérer si la ligne suivante
  est un autre heading / fin de fichier).
- si non trouvée : insérer un bloc `\n# Parent\n<key>\n` **avant** `# Description` (ou en fin
  de buffer si `# Description` absent).
- log + `status_message`.

> Note : `set_markdown_parent` reçoit l'`edit` token (TextCommand standard), contrairement à
> `_on_done`. C'est pourquoi l'insertion passe par `run_command`.

### 5. Snippet + `init_markdown_jira`

- Snippet `snippets/jira/jira-markdown.sublime-snippet` : ajouter, avant `# Description` :
  ```
  # Parent
  ${parent}
  ```
- `init_markdown_jira.py` : `args.setdefault("parent", "")` (vide par défaut →
  rétro-compatible, le buffer s'ouvre avec une section `# Parent` vide).

### 6. Settings

- `alfaco-atlassian.sublime-settings` (package) : `"jira_parent_types": ["Epic", "Story"]`.
- `templates/User/alfaco-atlassian.sublime-settings` : bloc JSONC documenté pour
  `jira_parent_types` (commentaire : types proposés par le popup parent ; vide non géré).

### 7. UI

- `plugin.py` : importer `SelectJiraParentCommand` et `SetMarkdownParentCommand`.
- `Context.sublime-menu` : `{ "caption": "choisir le parent (Epic/Story)", "command": "select_jira_parent" }`.
- `Main.sublime-menu` : `{ "caption": "Choisir le parent (Epic/Story)", "command": "select_jira_parent" }`.
- Keymaps (3 OS), famille `Ctrl+J` :
  - Linux/Windows : `{ "keys": ["ctrl+j", "ctrl+r"], "command": "select_jira_parent" }`
  - OSX : `{ "keys": ["super+j", "super+r"], "command": "select_jira_parent" }`

## Flux utilisateur

1. `select_jira_project` (pose `project_key`).
2. `Ctrl+J Ctrl+T` → buffer Markdown typé.
3. `Ctrl+J Ctrl+R` → popup des Epics/Stories du projet → sélection → la section `# Parent`
   du buffer est remplie avec la clé.
4. Édition (summary, description…), puis `Alt+M` → `create_jira_from_markdown` POST avec
   `"parent": {"key": "<KEY>"}`.

Variante manuelle : taper directement la clé sous `# Parent` sans passer par le popup.

## Tests (TDD hors-Sublime)

`plugins/AlfacoLib/tests/test_markdown_to_adf.py` :
- `# Parent` rempli → `payload["fields"]["parent"] == {"key": "MMPO-2"}`.
- `# Parent` vide ou absent → `"parent"` **absent** de `fields` (rétro-compat).
- `# Parent` reconnu par `_split_fields` (pas de `ValueError` « champ inconnu »).

`plugins/AlfacoLib/tests/test_atlassian_client.py` :
- `parse_parent_choices` : extrait `(key, "KEY — résumé (Type)")` depuis
  `{"issues": [...]}` ; liste vide → `[]` ; entrées sans `key` ignorées ; `data` mal formé → `[]`.

Les `*Command` (popup, édition buffer) ne sont pas testables hors-Sublime → validation
manuelle (cf. plan).

## Gestion d'erreurs

| Cas | Comportement |
|---|---|
| `project_key` vide | `error_message` : lancer `select_jira_project` d'abord. |
| login/token manquant | `error_message` (pattern `select_jira_project`). |
| Réseau / timeout | `error_message` + log. |
| HTTP ≠ 200 | `error_message` (status + extrait). |
| JSON invalide | `error_message`. |
| 0 parent trouvé | `message_dialog` explicite (aucune Epic/Story dans le projet). |

## Hors périmètre (YAGNI)

- Re-parentage de tickets existants (sous-projet #2).
- Validation que le type de l'issue créée est compatible avec le parent (Jira renvoie un
  400 explicite si incompatible — on laisse remonter le message).
- Pagination du popup parents (les projets visés tiennent dans une page `search`).
- Filtrage par statut (on liste tous les Epics/Stories, tri par date de création desc).

## Documentation à mettre à jour

- `docs/plugins/alfaco-atlassian.md` : commande, raccourci, champ `# Parent`, réglage
  `jira_parent_types`, workflow.
- `docs/usage.md` : index commandes + variante Markdown.
- `docs/configuration.md` : clé `jira_parent_types`.

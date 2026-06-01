# Spec — Re-parenter un ticket existant (sous-projet #2)

**Date** : 2026-06-01
**Statut** : validé (brainstorming)
**Branche** : `feat/jira-reparent-issue`

## Problème

Le sous-projet #1 permet de **créer** une issue rattachée à un parent (champ `# Parent`).
Il manque le pendant pour les tickets **déjà créés** : déplacer un ticket existant sous une
Epic ou une Story.

Sur le Jira Cloud de l'instance, re-parenter un ticket existant se fait par
`PUT /rest/api/{v}/issue/{KEY}` avec `{"fields": {"parent": {"key": "<PARENT-KEY>"}}}`
(même champ `parent` qu'en création ; Epic et Story sont au même niveau de hiérarchie
parent). Un `PUT` réussi renvoie **204 No Content** (pas de corps JSON).

## Décisions (brainstorming)

| Sujet | Décision |
|---|---|
| Choix du ticket à déplacer | **Saisie manuelle** de la clé via input panel (pas de listing). |
| Choix du parent de destination | **Popup Epic/Story** du projet courant (réutilise `parse_parent_choices` + `jira_parent_types` de #1). |
| Détacher (rendre orphelin) | **Hors périmètre** (YAGNI). Pas de `parent: null`. |
| Périmètre du popup parent | **Réutilise `jira_parent_types`** (défaut `["Epic", "Story"]`) — pas de nouveau réglage. |
| Payload | **Construit inline** dans la commande (pas de helper dédié testé). |
| Raccourci | `Ctrl+J Ctrl+M` / `Cmd+J Cmd+M` (M = Move ; chord distinct du `Ctrl+M` natif). |

## Architecture

C'est une **édition** d'un ticket existant, indépendante du flux Markdown. Aucune nouvelle
logique pure : on réutilise `parse_parent_choices` (déjà testé, AlfacoLib) et le pattern
`search` JQL de `select_jira_parent`.

### Commande `reparent_jira_issue.py` (NOUVELLE)

`ReparentJiraIssueCommand(sublime_plugin.TextCommand)` :

1. `cfg = plugin.config` ; lire `project_key` ; si vide → `error_message` (lancer
   `select_jira_project` d'abord) + `return`.
2. vérifier `jira_auth()` (login/password) ; manquant → `error_message` + `return`.
3. ouvrir un input panel :
   `self.view.window().show_input_panel("Clé du ticket à déplacer :", "", self._on_issue_key, None, None)`.
4. `_on_issue_key(issue_key)` :
   - `issue_key = issue_key.strip()` ; si vide → log annulation + `return`.
   - stocker `self._issue_key = issue_key`.
   - construire la JQL parents (identique à `select_jira_parent`) :
     `types = cfg.get("jira_parent_types", ["Epic", "Story"])` ;
     `clause = ", ".join('"%s"' % t for t in types)` ;
     `jql = 'project = "%s" AND issuetype in (%s) ORDER BY created DESC' % (project_key, clause)` ;
     `url = cfg.base_url() + "search?jql=" + quote(jql)`.
   - `call_rest(... verb="GET" ...)` avec garde-fous réseau/HTTP/JSON identiques à
     `select_jira_parent`.
   - `self._choices = parse_parent_choices(data)` ; si vide → `message_dialog` + `return`.
   - `show_popup_menu([label for _, label in self._choices], self._on_parent_done)`.
5. `_on_parent_done(index)` :
   - si `-1` → log annulation + `return`.
   - `parent_key = self._choices[index][0]`.
   - `payload = _json.dumps({"fields": {"parent": {"key": parent_key}}}, ensure_ascii=False)`.
   - `url = cfg.base_url() + "issue/" + self._issue_key`.
   - `call_rest(url, body=payload, auth=..., headers=..., verb="PUT", verify=...)`
     dans un `try/except (URLError, socket.timeout)`.
   - **Succès = 204** (ou tout 2xx) : `status_message` + log « `<issue>` rattaché à
     `<parent>` ». **Ne pas appeler `response.json()`** (corps vide sur 204).
   - status ≥ 400 : `error_message` avec `response.status_code` + `response.text[:500]`
     (Jira renvoie un message explicite si parent incompatible / ticket inexistant).

> `project_key` sert à lister les parents candidats ; le ticket à déplacer est désigné par
> sa clé saisie (on suppose qu'il appartient au même projet — cas d'usage visé).

### UI

- `plugin.py` : `from AlfacoAtlassian.commands.reparent_jira_issue import ReparentJiraIssueCommand  # noqa: E402, F401`.
- `Context.sublime-menu` : `{ "caption": "déplacer un ticket sous un parent", "command": "reparent_jira_issue" }`.
- `Main.sublime-menu` : `{ "caption": "Déplacer un ticket sous un parent", "command": "reparent_jira_issue" }`.
- Keymaps (3 OS), famille `Ctrl+J` :
  - Linux/Windows : `{ "keys": ["ctrl+j", "ctrl+m"], "command": "reparent_jira_issue" }`
  - OSX : `{ "keys": ["super+j", "super+m"], "command": "reparent_jira_issue" }`

## Flux utilisateur

1. `select_jira_project` (pose `project_key`).
2. `Ctrl+J Ctrl+M` → input panel « Clé du ticket à déplacer : » → saisir `MMPO-12` → Entrée.
3. Popup des Epics/Stories du projet → choisir `MMPO-2`.
4. `PUT /issue/MMPO-12` → 204 → message « MMPO-12 rattaché à MMPO-2 ».

## Gestion d'erreurs

| Cas | Comportement |
|---|---|
| `project_key` vide | `error_message` : lancer `select_jira_project` d'abord. |
| login/token manquant | `error_message` (pattern existant). |
| Clé ticket vide (input annulé) | log + `return`, sans bruit. |
| Erreur réseau / timeout (GET parents ou PUT) | `error_message` + log. |
| GET parents HTTP ≠ 200 / JSON invalide | `error_message`. |
| 0 parent trouvé | `message_dialog` explicite. |
| PUT 2xx (204) | succès : `status_message` + log. |
| PUT 400 (parent incompatible, type non hiérarchisable) | `error_message` avec le corps Jira. |
| PUT 404 (ticket inexistant) | `error_message` avec le corps Jira. |

## Tests

Aucune logique pure nouvelle à tester (`parse_parent_choices` couvert en #1 ; payload
trivial inline). La commande (input panel + popup + PUT) n'est pas testable hors-Sublime
(contrainte documentée) → **validation manuelle** dans Sublime.

> Si une régression de forme du payload devait être prévenue par un test, on extrairait
> `build_reparent_payload` en helper pur — non retenu ici (YAGNI, décision brainstorming).

## Hors périmètre (YAGNI)

- Détacher un ticket de son parent (`parent: null`).
- Listing/popup des tickets à déplacer (saisie manuelle retenue).
- Re-parentage en masse (plusieurs tickets d'un coup).
- Vérification côté client de la compatibilité type/parent (Jira renvoie un 400 explicite).
- Déplacer un ticket d'un autre projet que le projet courant (le popup parents est limité au
  projet courant ; le PUT lui-même n'est pas restreint, mais le cas n'est pas visé).

## Endpoint — point de vigilance

- `PUT /issue/{KEY}` est stable en API v2 et v3 → pas de risque « search/jql » ici.
- Le **GET parents** réutilise `search?jql=` : même réserve qu'en #1 (si 410/404, basculer
  sur `search/jql`). À confirmer en validation manuelle.

## Documentation à mettre à jour

- `docs/plugins/alfaco-atlassian.md` : commande `reparent_jira_issue`, raccourci.
- `docs/usage.md` : index des commandes + une ligne de workflow.

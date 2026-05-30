# Sélecteur de type d'issue → buffer Markdown — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter une commande AlfacoAtlassian qui liste les types d'issues du projet courant (popup) et ouvre un buffer Markdown pré-rempli avec le type choisi.

**Architecture:** Un helper pur `parse_issue_type_names` dans `AlfacoLib/atlassian_client.py` (testé hors-Sublime) extrait/déduplique les noms de types depuis `GET /project/{key}?expand=issueTypes`. Une nouvelle commande `SelectJiraIssueTypeCommand` fait l'appel REST, affiche le popup, et délègue l'ouverture du buffer à la commande existante `init_markdown_jira` (en lui passant `type`). Le snippet gagne une variable `${type}` (défaut `Task`).

**Tech Stack:** Python 3.8 (plugin host Sublime Text 4), `urllib` (stdlib), pytest hors-Sublime, fichiers `.sublime-keymap` / `.sublime-menu` / `.sublime-snippet`.

**Contraintes projet (rappel) :** code/commentaires/captions en **français** ; une commande = un fichier dans `commands/`, importée dans `plugin.py` ; mettre à jour **les 3 keymaps OS** ; commits fréquents ; pas de `--no-verify`.

---

## File Structure

- **Modify** `plugins/AlfacoLib/atlassian_client.py` — ajout de `parse_issue_type_names(data)` (logique pure).
- **Modify** `plugins/AlfacoLib/tests/test_atlassian_client.py` — tests du helper.
- **Modify** `plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet` — `Task` → `${type}`.
- **Modify** `plugins/AlfacoAtlassian/commands/init_markdown_jira.py` — `args.setdefault("type", "Task")`.
- **Create** `plugins/AlfacoAtlassian/commands/select_jira_issue_type.py` — nouvelle commande.
- **Modify** `plugins/AlfacoAtlassian/plugin.py` — import de la commande.
- **Modify** `plugins/AlfacoAtlassian/Context.sublime-menu` — entrée clic droit.
- **Modify** `plugins/AlfacoAtlassian/Main.sublime-menu` — entrée Tools.
- **Modify** `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap` — chord `ctrl+j ctrl+t`.
- **Modify** `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap` — chord `ctrl+j ctrl+t`.
- **Modify** `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap` — chord `super+j super+t`.
- **Modify** `docs/plugins/alfaco-atlassian.md`, `docs/usage.md` — doc.

---

## Task 1 : helper `parse_issue_type_names` (TDD)

**Files:**
- Test: `plugins/AlfacoLib/tests/test_atlassian_client.py`
- Modify: `plugins/AlfacoLib/atlassian_client.py`

- [ ] **Step 1 : écrire les tests qui échouent**

Ajouter à la fin de `plugins/AlfacoLib/tests/test_atlassian_client.py` :

```python
def test_parse_issue_type_names_from_project_object():
    data = {
        "key": "GDQ",
        "issueTypes": [
            {"id": "1", "name": "Tâche", "subtask": False},
            {"id": "2", "name": "Sous-tâche", "subtask": True},
            {"id": "3", "name": "Story", "subtask": False},
        ],
    }
    assert atlassian_client.parse_issue_type_names(data) == [
        "Tâche",
        "Sous-tâche",
        "Story",
    ]


def test_parse_issue_type_names_deduplicates_by_name_preserving_order():
    data = {
        "issueTypes": [
            {"id": "10105", "name": "Tâche"},
            {"id": "10179", "name": "Story"},
            {"id": "10180", "name": "Tâche"},
            {"id": "10181", "name": "Epic"},
        ]
    }
    assert atlassian_client.parse_issue_type_names(data) == [
        "Tâche",
        "Story",
        "Epic",
    ]


def test_parse_issue_type_names_accepts_direct_list():
    data = [{"name": "Bug"}, {"name": "Task"}]
    assert atlassian_client.parse_issue_type_names(data) == ["Bug", "Task"]


def test_parse_issue_type_names_empty_or_missing():
    assert atlassian_client.parse_issue_type_names({}) == []
    assert atlassian_client.parse_issue_type_names({"issueTypes": []}) == []
    assert atlassian_client.parse_issue_type_names(None) == []


def test_parse_issue_type_names_ignores_entries_without_name():
    data = {"issueTypes": [{"id": "1"}, {"name": "Task"}, {"name": ""}]}
    assert atlassian_client.parse_issue_type_names(data) == ["Task"]
```

- [ ] **Step 2 : lancer les tests pour vérifier l'échec**

Run: `pytest plugins/AlfacoLib/tests/test_atlassian_client.py -k parse_issue_type_names -v`
Expected: FAIL — `AttributeError: module 'AlfacoLib.atlassian_client' has no attribute 'parse_issue_type_names'`.

- [ ] **Step 3 : implémenter le helper**

Ajouter à la fin de `plugins/AlfacoLib/atlassian_client.py` :

```python
def parse_issue_type_names(data):
    """Extrait les noms de types d'issues d'une réponse Jira.

    `data` est l'objet projet décodé (dict) issu de
    `GET /project/{key}?expand=issueTypes`, avec une clé `issueTypes` (liste).
    Tolère aussi une liste de types passée directement.

    Retourne la liste des noms, dédupliquée (premier vu gagné) et dans l'ordre
    d'apparition. Inclut les types `subtask`. Ignore les entrées sans `name`
    non vide. Retourne `[]` si `data` est None/vide/mal formé.
    """
    if isinstance(data, dict):
        types = data.get("issueTypes") or []
    elif isinstance(data, list):
        types = data
    else:
        return []

    names = []
    seen = set()
    for t in types:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names
```

- [ ] **Step 4 : lancer les tests pour vérifier le succès**

Run: `pytest plugins/AlfacoLib/tests/test_atlassian_client.py -k parse_issue_type_names -v`
Expected: PASS (5 tests).

- [ ] **Step 5 : commit**

```bash
git add plugins/AlfacoLib/atlassian_client.py plugins/AlfacoLib/tests/test_atlassian_client.py
git commit -m "feat(lib): parse_issue_type_names (dédup noms de types Jira)"
```

---

## Task 2 : variable `${type}` dans le snippet + défaut dans init_markdown_jira

Pas de test unitaire : snippets et `*Command` ne sont pas testables hors-Sublime (cf. CLAUDE.md). Validation manuelle dans Sublime (Task 6).

**Files:**
- Modify: `plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet`
- Modify: `plugins/AlfacoAtlassian/commands/init_markdown_jira.py`

- [ ] **Step 1 : remplacer `Task` par `${type}` dans le snippet**

Dans `plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet`, remplacer le bloc :

```
# Type
Task
```

par :

```
# Type
${type}
```

(Ne pas toucher au reste du fichier.)

- [ ] **Step 2 : poser le défaut `type` dans init_markdown_jira**

Dans `plugins/AlfacoAtlassian/commands/init_markdown_jira.py`, après la ligne
`args["jira_key"] = _atlassian_plugin.config.get("project_key", "")` (ligne 26),
ajouter :

```python
        args.setdefault("type", "Task")
```

Résultat attendu (extrait) :

```python
        args["jira_key"] = _atlassian_plugin.config.get("project_key", "")
        args.setdefault("type", "Task")
```

Le défaut `"Task"` préserve le comportement de `Ctrl+M` (appel sans `type`).

- [ ] **Step 3 : vérifier que la suite de tests reste verte**

Run: `make test`
Expected: PASS (aucune régression ; ces fichiers ne sont pas couverts par les tests).

- [ ] **Step 4 : commit**

```bash
git add plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet plugins/AlfacoAtlassian/commands/init_markdown_jira.py
git commit -m "feat(atlassian): variable \${type} dans le template Markdown (défaut Task)"
```

---

## Task 3 : commande `select_jira_issue_type`

Pas de test unitaire (TextCommand non testable hors-Sublime) ; la logique testable est dans `parse_issue_type_names` (Task 1). Validation manuelle en Task 6.

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/select_jira_issue_type.py`
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1 : créer le fichier de commande**

Créer `plugins/AlfacoAtlassian/commands/select_jira_issue_type.py` avec :

```python
# -*- coding: utf-8 -*-
"""GET /project/{key}?expand=issueTypes, popup des types, ouvre un buffer Markdown.

À la sélection, délègue à la commande init_markdown_jira en lui passant le nom
du type choisi (champ `# Type` du template). Le payload de création référence le
type par son nom, donc l'id n'est pas nécessaire ; les noms en doublon sont
dédupliqués par parse_issue_type_names.
"""
import socket
from urllib.error import URLError

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, parse_issue_type_names


class SelectJiraIssueTypeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config

        project_key = cfg.get("project_key", "")
        if not project_key:
            _atlassian_plugin.log.error("project_key vide : select_jira_project requis d'abord")
            sublime.error_message(
                "AlfacoAtlassian : aucun projet courant.\n\n"
                "Lance d'abord « Sélectionner projet Jira » (select_jira_project)."
            )
            return

        login, password = cfg.jira_auth()
        if not login or not password:
            _atlassian_plugin.log.error(
                f"jira_login/jira_password vide (login={login!r}, password={'(set)' if password else '(empty)'})"
            )
            sublime.error_message(
                "AlfacoAtlassian : `jira_login` ou `jira_password` manquant.\n\n"
                "Renseigner un email et un token API dans :\n"
                "Preferences → Package Settings → AlfacoAtlassian → Settings – User"
            )
            return

        url = cfg.base_url() + "project/" + project_key + "?expand=issueTypes"
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération types depuis {url}…")

        try:
            response = call_rest(
                url,
                body=None,
                auth=(login, password),
                headers=cfg.get("headers", {"Accept": "application/json"}),
                verb="GET",
                verify=cfg.get("tls_verify", True),
            )
        except (URLError, socket.timeout) as e:
            _atlassian_plugin.log.error(f"erreur réseau sur {url} : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : impossible de joindre {url}\n\n"
                f"{e}\n\nVérifier `default_organisation` et la connectivité."
            )
            return

        _atlassian_plugin.log.info(
            f"GET {url} → {response.status_code} ({len(response.text)} bytes)"
        )

        if response.status_code != 200:
            _atlassian_plugin.log.error(
                f"GET {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : la requête a échoué.\n\n"
                f"HTTP {response.status_code}\n{response.text[:500]}"
            )
            return

        try:
            data = response.json()
        except ValueError as e:
            _atlassian_plugin.log.error(
                f"réponse non-JSON ({len(response.text)} bytes) : {e} | preview={response.text[:200]!r}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : réponse non-JSON.\n\n{response.text[:500]}"
            )
            return

        self._items = parse_issue_type_names(data)
        if not self._items:
            _atlassian_plugin.log.warn(
                f"{url} : 0 type (status=200, preview={response.text[:200]!r})"
            )
            sublime.message_dialog(
                f"AlfacoAtlassian : aucun type d'issue retourné pour {project_key}."
            )
            return

        _atlassian_plugin.log.info(f"{len(self._items)} type(s) prêts pour le popup")
        sublime.status_message(f"AlfacoAtlassian : {len(self._items)} type(s)")
        self.view.show_popup_menu(self._items, self._on_done)

    def _on_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection type annulée")
            return
        type_name = self._items[index]
        _atlassian_plugin.log.info(f"type sélectionné : {type_name}")
        self.view.run_command("init_markdown_jira", {"type": type_name})
```

- [ ] **Step 2 : enregistrer la commande dans plugin.py**

Dans `plugins/AlfacoAtlassian/plugin.py`, après la ligne d'import de
`InsertCurrentOrganisationCommand` (ligne 46), ajouter :

```python
from AlfacoAtlassian.commands.select_jira_issue_type import SelectJiraIssueTypeCommand  # noqa: E402,F401
```

- [ ] **Step 3 : vérifier l'import Python (sanity check hors-Sublime)**

Run: `python3 -c "import ast; ast.parse(open('plugins/AlfacoAtlassian/commands/select_jira_issue_type.py').read()); print('OK')"`
Expected: `OK` (pas d'erreur de syntaxe).

- [ ] **Step 4 : vérifier que la suite de tests reste verte**

Run: `make test`
Expected: PASS (aucune régression).

- [ ] **Step 5 : commit**

```bash
git add plugins/AlfacoAtlassian/commands/select_jira_issue_type.py plugins/AlfacoAtlassian/plugin.py
git commit -m "feat(atlassian): commande select_jira_issue_type (popup des types du projet)"
```

---

## Task 4 : intégration UI (menus + 3 keymaps)

**Files:**
- Modify: `plugins/AlfacoAtlassian/Context.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Main.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`

- [ ] **Step 1 : ajouter l'entrée au menu contextuel**

Dans `plugins/AlfacoAtlassian/Context.sublime-menu`, ajouter une entrée dans le tableau
`children` après `{ "caption": "init Markdown Jira", "command": "init_markdown_jira" },`
(ajouter une virgule à la ligne précédente si nécessaire) :

```json
            { "caption": "créer issue (choisir le type)", "command": "select_jira_issue_type" },
```

- [ ] **Step 2 : ajouter l'entrée au menu Tools**

Dans `plugins/AlfacoAtlassian/Main.sublime-menu`, dans le tableau `children` du nœud
`alfaco-atlassian`, après la ligne
`{ "caption": "Initialiser Markdown Jira", "command": "init_markdown_jira" },`
ajouter :

```json
                            { "caption": "Créer issue (choisir le type)", "command": "select_jira_issue_type" },
```

(Vérifier que la virgule de fin de la ligne précédente est présente et qu'aucune
virgule traînante n'apparaît avant `]`.)

- [ ] **Step 3 : ajouter le chord dans le keymap Linux**

Dans `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`, dans le bloc « Famille Ctrl+J »,
après la ligne `{ "keys": ["ctrl+j", "p"], "command": "insert_current_project" },` ajouter :

```json
    { "keys": ["ctrl+j", "ctrl+t"], "command": "select_jira_issue_type" },
```

- [ ] **Step 4 : ajouter le chord dans le keymap Windows**

Dans `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`, au même endroit
(après `insert_current_project`), ajouter la ligne identique :

```json
    { "keys": ["ctrl+j", "ctrl+t"], "command": "select_jira_issue_type" },
```

- [ ] **Step 5 : ajouter le chord dans le keymap OSX**

Dans `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`, dans le bloc « Famille Cmd+J »,
après la ligne `{ "keys": ["super+j", "p"], "command": "insert_current_project" },` ajouter :

```json
    { "keys": ["super+j", "super+t"], "command": "select_jira_issue_type" },
```

- [ ] **Step 6 : valider le JSON des 5 fichiers**

Run:
```bash
python3 -c "import json,glob; [json.load(open(f)) for f in ['plugins/AlfacoAtlassian/Context.sublime-menu','plugins/AlfacoAtlassian/Main.sublime-menu','plugins/AlfacoAtlassian/Default (Linux).sublime-keymap','plugins/AlfacoAtlassian/Default (Windows).sublime-keymap','plugins/AlfacoAtlassian/Default (OSX).sublime-keymap']]; print('JSON OK')"
```
Expected: `JSON OK` (les `.sublime-keymap`/`.sublime-menu` sont du JSON strict sans commentaires ici ; si un fichier contient des commentaires `//`, le valider visuellement à la place).

> Note : les keymaps contiennent des commentaires `//` → `json.load` échouera dessus. Dans ce cas, valider visuellement l'équilibrage des accolades/crochets et l'absence de virgule traînante, et se fier à la validation Sublime (Task 6).

- [ ] **Step 7 : commit**

```bash
git add "plugins/AlfacoAtlassian/Context.sublime-menu" "plugins/AlfacoAtlassian/Main.sublime-menu" "plugins/AlfacoAtlassian/Default (Linux).sublime-keymap" "plugins/AlfacoAtlassian/Default (Windows).sublime-keymap" "plugins/AlfacoAtlassian/Default (OSX).sublime-keymap"
git commit -m "feat(atlassian): menus + raccourci Ctrl+J Ctrl+T pour select_jira_issue_type"
```

---

## Task 5 : documentation

**Files:**
- Modify: `docs/plugins/alfaco-atlassian.md`
- Modify: `docs/usage.md`

- [ ] **Step 1 : documenter la commande dans alfaco-atlassian.md**

Dans `docs/plugins/alfaco-atlassian.md`, table « Commandes », ajouter après la ligne
`insert_current_organisation` :

```markdown
| `select_jira_issue_type` | Popup des types d'issues du projet courant (`GET /project/{KEY}?expand=issueTypes`, noms dédupliqués) ; à la sélection, ouvre un buffer Markdown pré-rempli avec ce type. |
```

Dans la table « Raccourcis » du même fichier, ajouter une ligne :

```markdown
| `Ctrl+J Ctrl+T` / `Cmd+J Cmd+T` | tous | `select_jira_issue_type` (popup des types du projet, ouvre le buffer Markdown) |
```

- [ ] **Step 2 : mettre à jour usage.md**

Dans `docs/usage.md`, section « Index des commandes » → « AlfacoAtlassian », ajouter
`select_jira_issue_type` à la liste des commandes (après `insert_current_organisation`).

Dans la sous-section « Variante Markdown », ajouter une puce après l'étape 1 :

```markdown
   - *Alternative typée* : `select_jira_issue_type` (`Ctrl+J Ctrl+T`) propose les types du projet courant et ouvre le buffer avec `# Type` déjà rempli.
```

- [ ] **Step 3 : commit**

```bash
git add docs/plugins/alfaco-atlassian.md docs/usage.md
git commit -m "docs(atlassian): documenter select_jira_issue_type + raccourci Ctrl+J Ctrl+T"
```

---

## Task 6 : validation manuelle dans Sublime (humain)

Non automatisable. À réaliser par l'utilisateur après déploiement (`make install`).

- [ ] `make install` puis redémarrer Sublime.
- [ ] `select_organisation` puis `select_jira_project` (poser org + projet).
- [ ] `Ctrl+J Ctrl+T` → le popup liste les types du projet (noms dédupliqués) ; sélectionner « Story ».
- [ ] Un buffer Markdown s'ouvre avec `# Type` suivi de `Story`, `# Organisation` rempli, dates auto.
- [ ] `Alt+M` → le ticket est créé avec le bon type (vérifier dans Jira).
- [ ] Vérifier le menu clic droit et `Tools → Alfaco → Atlassian` contiennent « Créer issue (choisir le type) ».
- [ ] Sans projet courant : `Ctrl+J Ctrl+T` affiche le message d'erreur invitant à lancer `select_jira_project`.

---

## Self-Review (auteur du plan)

- **Couverture du spec** : helper (T1) ✓, snippet+défaut (T2) ✓, commande+enregistrement (T3) ✓, menus+keymaps 3 OS (T4) ✓, docs (T5) ✓, validation manuelle (T6) ✓. Gestion d'erreurs du spec couverte par le code de T3 (project_key vide, auth, réseau, HTTP≠200, JSON, 0 type).
- **Placeholders** : aucun — tout le code et toutes les commandes sont fournis.
- **Cohérence des types** : `parse_issue_type_names(data) -> list[str]` utilisé tel quel en T3 ; `init_markdown_jira` reçoit `{"type": <str>}` cohérent avec `args.setdefault("type", "Task")` (T2) et `${type}` du snippet (T2).
